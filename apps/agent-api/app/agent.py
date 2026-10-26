"""Le graphe de Wakil : le LLM choisit l'outil, le code appelle la banque et écrit la réponse.

Pour un paiement ou un virement, le graphe s'arrête (interrupt) et attend la réponse du client :
aucune opération sans un « oui » explicite.
"""

import os
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal, TypedDict

import httpx
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

from app import banque, reponses

SYSTEME = (
    "Tu es Wakil, l'assistant de la Banque Atlas Démo (banque fictive). "
    "Le client écrit en darija marocaine, en lettres arabes ou latines, souvent mélangée au français. "
    "Si la demande concerne son compte, appelle l'outil adapté. "
    "Pour payer une facture ou faire un virement, appelle l'outil avec ses paramètres : le client confirmera "
    "toujours avant que la banque n'exécute quoi que ce soit. N'invente jamais un montant ni un bénéficiaire. "
    "Sinon, réponds en darija que tu ne t'occupes que de la banque."
)


def description(nom: str, texte: str, parametres: dict | None = None) -> dict:
    """Ce que le LLM voit d'un outil : un nom, une description et ses paramètres. Jamais le client_id : il vient
    de la session."""
    return {
        "type": "function",
        "function": {
            "name": nom,
            "description": texte,
            "parameters": {"type": "object", "properties": parametres or {}, "required": list(parametres or {})},
        },
    }


# Les fournisseurs, tous fictifs. Le LLM choisit une clé courte, le code la traduit en nom exact.
FOURNISSEURS = {"eau_electricite": "Eau & Électricité (démo)", "internet": "Internet (démo)", "mobile": "Mobile (démo)"}

# Liste fermée : le LLM ne peut choisir que parmi ces outils. Les trois premiers lisent, les deux derniers paient.
OUTILS = {
    "consulter_solde": (banque.solde, reponses.solde),
    "lister_transactions": (banque.transactions, reponses.transactions),
    "lister_factures": (banque.factures_impayees, reponses.factures),
}
OPERATIONS = {"payer_facture": "paiement", "faire_virement": "virement"}
DESCRIPTIONS = [
    description("consulter_solde", "Donne le solde actuel du compte du client."),
    description(
        "lister_transactions", "Liste les dernières opérations du compte du client (dépenses, virements reçus)."
    ),
    description("lister_factures", "Montre les factures impayées du client, sans rien payer."),
    description(
        "payer_facture",
        "Paye une facture impayée du client (eau et électricité, internet, mobile). En darija, le client dit "
        "« khelless », « khalles », « nkhelless » ou « خلص ». Le client confirmera avant le paiement.",
        {
            "fournisseur": {
                "type": "string",
                "enum": list(FOURNISSEURS),
                "description": "eau_electricite pour l'eau ou l'électricité, internet, ou mobile (téléphone).",
            }
        },
    ),
    description(
        "faire_virement",
        "Vire de l'argent à un bénéficiaire déjà enregistré par le client. En darija, le client dit « sifet », "
        "« sift », « 7awel » ou « صيفط ». Le client confirmera avant le virement.",
        {
            "beneficiaire": {"type": "string", "description": "Le prénom ou le nom du bénéficiaire, tel qu'écrit."},
            "montant": {"type": "number", "description": "Le montant en dirhams (DH)."},
        },
    ),
]
SALUTATIONS = {"salam", "slm", "salam 3likom", "salam alaykom", "سلام", "السلام عليكم"}
# Accusés de réception et remerciements : ni une demande, ni du hors-sujet.
POLITESSES = {
    "mzyan", "mzn", "mzyane", "مزيان", "merci", "merci bcp", "merci beaucoup", "chokran", "choukran", "شكرا",
    "ok", "okay", "d'accord", "dacc", "safi", "tres bien", "très bien", "top", "barak allah fik", "lah yjazik bikhir",
}  # fmt: skip
# Réponses à « Wach nconfirmi ? ». Liste fermée, lue par le code : le LLM ne décide jamais d'une confirmation.
OUI = {"oui", "oui, confirmer", "ah", "iyeh", "iyyeh", "wakha", "yes", "ok", "confirmer", "نعم", "اه", "واخا"}
NON = {"non", "non, annuler", "la", "lla", "no", "annuler", "لا"}

# Nouveauté : LangChain remplace notre appel HTTP fait à la main vers Ollama.
llm = ChatOllama(
    model=os.environ.get("WAKIL_MODELE", "qwen3:4b-instruct"),
    temperature=0,
    num_predict=100,  # assez pour un appel d'outil ; son texte libre ne nous sert pas
).bind_tools(DESCRIPTIONS)


HISTORIQUE = 6  # le LLM voit les 6 derniers messages (3 échanges) : assez pour « c'est tout ? », et rapide


class Etat(TypedDict, total=False):
    client_id: int  # vient de la session, jamais du LLM
    messages: Annotated[list[AnyMessage], add_messages]  # l'historique : chaque case AJOUTE au lieu de remplacer
    # Les champs suivants ne valent que pour le message en cours (remis à zéro par nouveau_tour).
    demande: str
    outil: str | None
    arguments: dict  # les paramètres choisis par le LLM (fournisseur, bénéficiaire, montant)
    resultat: dict | list | None
    operation: dict | None  # l'opération vérifiée à blanc, qui attend la réponse du client
    confirmation: Literal["oui", "non"] | None
    erreur: bool
    reponse: str


def nouveau_tour(demande: str, client_id: int) -> dict:
    """Entrée d'un nouveau message. Sans cette remise à zéro, la mémoire garderait l'erreur ou l'outil du message précédent."""
    return {
        "client_id": client_id,
        "messages": [HumanMessage(demande)],
        "demande": demande,
        "outil": None,
        "arguments": {},
        "resultat": None,
        "operation": None,
        "confirmation": None,
        "erreur": False,
        "reponse": "",
    }


def config(client_id: int, conversation_id: str) -> dict:
    """Le fil de conversation est rangé sous l'id du client : un autre client ne peut pas le relire, même en devinant l'id."""
    return {"configurable": {"thread_id": f"{client_id}:{conversation_id}"}}


def prochaine_entree(graphe, demande: str, client_id: int, conf: dict) -> dict | Command:
    """Si une opération attend « Wach nconfirmi ? », le message du client est sa réponse : on reprend le graphe là où
    il s'était arrêté (Command(resume=…)). Sinon, c'est une nouvelle demande."""
    if graphe.get_state(conf).interrupts:
        return Command(resume=demande)
    return nouveau_tour(demande, client_id)


def dire(texte: str) -> dict:
    """La réponse de Wakil, ajoutée aussi à l'historique pour les messages suivants."""
    return {"reponse": texte, "messages": [AIMessage(texte)]}


def simplifier(texte: str) -> str:
    """« Fatima », « fatima » et « Fâtima » se valent : minuscules, sans accents, sans ponctuation autour."""
    sans_accents = "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
    return sans_accents.lower().strip().strip("!?.,;:، ")


# Petits mots que le LLM laisse parfois devant le nom : « sifet 500 l Fatima » donne « l Fatima » (l = à, en darija).
PARTICULES = {"l", "li", "le", "la", "a", "ila", "ل"}


def trouver_beneficiaires(beneficiaires: list[dict], nom: str) -> list[dict]:
    """Les bénéficiaires dont le nom contient tous les mots donnés (« Fatima », « fatima lahlou », « l Fatima »)."""
    mots = [mot for mot in simplifier(nom).replace("'", " ").split() if mot not in PARTICULES]
    if not mots:
        return []
    exacts = [b for b in beneficiaires if simplifier(b["nom"]).split() == mots]
    return exacts or [b for b in beneficiaires if set(mots) <= set(simplifier(b["nom"]).split())]


def lire_montant(valeur) -> Decimal | None:
    """Le montant donné par le LLM (500, « 500 DH », « 1 000,50 ») en Decimal au centime, ou None s'il n'est pas valable.

    On enlève seulement les espaces et « DH » : un « -50 » doit rester négatif, donc refusé, et pas devenir 50.
    """
    texte = re.sub(r"[\s\u00a0\u202f]", "", str(valeur)).replace(",", ".")
    texte = re.sub(r"(?i)(dh|mad|dirhams?)$", "", texte)
    try:
        montant = Decimal(texte)
        if not montant.is_finite() or montant != montant.quantize(Decimal("0.01")):  # « NaN », ou 12,345 DH
            return None
        montant = montant.quantize(Decimal("0.01"))
    except InvalidOperation:
        return None
    return montant if montant > 0 else None


def avant_comprendre(etat: Etat) -> Literal["saluer", "remercier", "comprendre"]:
    """Aiguillage de départ : une salutation ou une politesse seule ne passe pas par le LLM."""
    texte = etat["demande"].strip().lower().rstrip("!?.، ")
    if texte in SALUTATIONS:
        return "saluer"
    if texte in POLITESSES:
        return "remercier"
    return "comprendre"


def saluer(etat: Etat) -> dict:
    return dire(reponses.SALUT)


def remercier(etat: Etat) -> dict:
    return dire(reponses.POLITESSE)


def comprendre(etat: Etat) -> dict:
    """Le LLM lit la demande, avec les derniers messages pour le contexte, et choisit un outil (et ses paramètres) ou aucun."""
    message = llm.invoke([SystemMessage(SYSTEME), *etat["messages"][-HISTORIQUE:]])
    appel = message.tool_calls[0] if message.tool_calls else None
    # Un nom d'outil inventé par le LLM est traité comme « aucun outil ».
    if appel is None or (appel["name"] not in OUTILS and appel["name"] not in OPERATIONS):
        return {"outil": None}
    return {"outil": appel["name"], "arguments": appel.get("args") or {}}


def apres_comprendre(etat: Etat) -> Literal["executer_outil", "preparer_operation", "refuser"]:
    if etat["outil"] in OPERATIONS:
        return "preparer_operation"
    return "executer_outil" if etat["outil"] else "refuser"


def executer_outil(etat: Etat) -> dict:
    """Le code appelle bank-api avec le client_id de la session."""
    appeler, _ = OUTILS[etat["outil"]]
    try:
        return {"resultat": appeler(etat["client_id"])}
    except httpx.HTTPError:
        return {"erreur": True}


def repondre(etat: Etat) -> dict:
    """Le code met le résultat de la banque en phrase."""
    if etat.get("erreur"):
        return dire(reponses.ERREUR)
    _, formuler = OUTILS[etat["outil"]]
    return dire(formuler(etat["resultat"]))


def refuser(etat: Etat) -> dict:
    return dire(reponses.REFUS)


def preparer_operation(etat: Etat) -> dict:
    """Trouve la facture ou le bénéficiaire, puis demande à la banque une vérification à blanc.

    Le résultat devient la carte « Wach nconfirmi ? ». Si la banque refuse déjà (solde, plafond…), Wakil le dit tout
    de suite au lieu de faire confirmer une opération vouée à l'échec. Rien n'est payé ici.
    """
    client_id, arguments = etat["client_id"], etat.get("arguments") or {}
    type_operation = OPERATIONS[etat["outil"]]
    try:
        if type_operation == "paiement":
            fournisseur = FOURNISSEURS.get(arguments.get("fournisseur"))
            if fournisseur is None:
                return dire(reponses.QUEL_FOURNISSEUR)
            # S'il y en a plusieurs du même fournisseur, la plus ancienne d'abord (la banque les rend par id).
            facture = next((f for f in banque.factures_impayees(client_id) if f["fournisseur"] == fournisseur), None)
            if facture is None:
                return dire(reponses.pas_de_facture(fournisseur))
            simulation = banque.payer(client_id, facture["id"], simulation=True)
        else:
            nom = str(arguments.get("beneficiaire") or "").strip()
            if not nom:
                return dire(reponses.QUEL_BENEFICIAIRE)
            candidats = trouver_beneficiaires(banque.beneficiaires(client_id), nom)
            if not candidats:
                return dire(reponses.beneficiaire_inconnu(nom))
            if len(candidats) > 1:
                return dire(reponses.beneficiaire_ambigu(nom))
            montant = lire_montant(arguments.get("montant"))
            if montant is None:
                return dire(reponses.QUEL_MONTANT)
            simulation = banque.virer(client_id, candidats[0]["id"], montant, simulation=True)
            simulation["beneficiaire_id"] = candidats[0]["id"]
    except banque.RefusBanque as refus:
        return dire(reponses.refus(type_operation, refus.detail))
    except httpx.HTTPError:
        return {"erreur": True, **dire(reponses.ERREUR)}

    operation = {"type": type_operation, **simulation}
    operation["texte"] = reponses.confirmation(operation)
    # La question entre dans l'historique ; la réponse du client y entrera à la reprise.
    return {"operation": operation, "messages": [AIMessage(operation["texte"])]}


def apres_preparation(etat: Etat) -> Literal["demander_confirmation", "__end__"]:
    return "demander_confirmation" if etat.get("operation") else END


def demander_confirmation(etat: Etat) -> dict:
    """Le graphe s'arrête ici (interrupt) jusqu'à la réponse du client, même si le serveur redémarre entre-temps.

    À la reprise, cette case recommence depuis le début : rien avant interrupt() ne doit avoir d'effet. C'est pour cela
    que la vérification à blanc est dans la case d'avant.
    """
    reponse = str(interrupt(etat["operation"]))  # ⏸ la valeur part au front ; à la reprise, c'est la réponse du client
    mot = simplifier(reponse)
    decision = "oui" if mot in OUI else "non" if mot in NON else None
    return {"confirmation": decision, "messages": [HumanMessage(reponse)]}


def apres_confirmation(etat: Etat) -> Literal["executer_operation", "annuler"]:
    return "executer_operation" if etat.get("confirmation") == "oui" else "annuler"


def executer_operation(etat: Etat) -> dict:
    """Le client a dit oui : la banque exécute pour de vrai, en revérifiant toutes ses règles."""
    operation, client_id = etat["operation"], etat["client_id"]
    # À la reprise, la case « comprendre » n'est pas rejouée : on redonne l'outil pour l'événement envoyé au front.
    outil = {"outil": etat["outil"]}
    try:
        if operation["type"] == "paiement":
            resultat = banque.payer(client_id, operation["facture_id"])
        else:
            resultat = banque.virer(client_id, operation["beneficiaire_id"], Decimal(operation["montant"]))
    except banque.RefusBanque as refus:  # la situation a changé entre la carte et le « oui »
        return {**outil, **dire(reponses.refus(operation["type"], refus.detail))}
    except httpx.HTTPError:
        return {**outil, "erreur": True, **dire(reponses.ERREUR_OPERATION)}
    return {**outil, "resultat": resultat, **dire(reponses.operation_faite(operation["type"], resultat))}


def annuler(etat: Etat) -> dict:
    """« La », ou une réponse qui n'est ni oui ni non : on ne touche à rien."""
    outil = {"outil": etat["outil"]}
    if etat.get("confirmation") == "non":
        return {**outil, **dire(reponses.ANNULEE[etat["operation"]["type"]])}
    return {**outil, **dire(reponses.CONFIRMATION_INCOMPRISE)}


graphe = StateGraph(Etat)
graphe.add_node("saluer", saluer)
graphe.add_node("remercier", remercier)
graphe.add_node("comprendre", comprendre)
graphe.add_node("executer_outil", executer_outil)
graphe.add_node("repondre", repondre)
graphe.add_node("refuser", refuser)
graphe.add_node("preparer_operation", preparer_operation)
graphe.add_node("demander_confirmation", demander_confirmation)
graphe.add_node("executer_operation", executer_operation)
graphe.add_node("annuler", annuler)
graphe.add_conditional_edges(START, avant_comprendre)
graphe.add_conditional_edges("comprendre", apres_comprendre)
graphe.add_edge("executer_outil", "repondre")
graphe.add_conditional_edges("preparer_operation", apres_preparation)
graphe.add_conditional_edges("demander_confirmation", apres_confirmation)
for fin in ("saluer", "remercier", "repondre", "refuser", "executer_operation", "annuler"):
    graphe.add_edge(fin, END)


def construire(memoire: BaseCheckpointSaver):
    """Le graphe prêt à tourner, avec l'endroit où il range ses conversations (le « checkpointer »)."""
    return graphe.compile(checkpointer=memoire)


# Par défaut, en mémoire vive (tests, terminal). agent-api le remplace par PostgreSQL au démarrage (voir memoire.py).
wakil = construire(InMemorySaver())
