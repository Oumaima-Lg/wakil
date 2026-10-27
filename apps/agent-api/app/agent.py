"""Le graphe de Wakil : le LLM choisit l'outil, le code appelle la banque et écrit la réponse.

Pour un paiement ou un virement, le graphe s'arrête (interrupt) et attend la réponse du client :
aucune opération sans un « oui » explicite.
"""

import os
import unicodedata
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

from app import outils, reponses

SYSTEME = (
    "Tu es Wakil, l'assistant de la Banque Atlas Démo (banque fictive). "
    "Le client écrit en darija marocaine, en lettres arabes ou latines, souvent mélangée au français. "
    "Si la demande concerne son compte, appelle l'outil adapté. "
    "Pour payer une facture ou faire un virement, appelle l'outil avec ses paramètres : le client confirmera "
    "toujours avant que la banque n'exécute quoi que ce soit. N'invente jamais un montant ni un bénéficiaire. "
    "Sinon, réponds en darija que tu ne t'occupes que de la banque."
)


def lire(nom: str, cle: str | None = None):
    """Un outil de lecture du serveur MCP. cle : la liste est rangée sous ce nom (« transactions », « factures »)."""

    def appeler(client_id: int):
        donnees = outils.appeler(client_id, nom, {})
        return donnees[cle] if cle else donnees

    return appeler


# Liste fermée : le LLM ne peut choisir que parmi ces outils, dont le serveur MCP donne la description et le schéma.
# Les trois premiers lisent ; les deux derniers déplacent de l'argent, donc passent par la carte de confirmation.
OUTILS = {
    "consulter_solde": (lire("consulter_solde"), reponses.solde),
    "lister_transactions": (lire("lister_transactions", "transactions"), reponses.transactions),
    "lister_factures": (lire("lister_factures", "factures"), reponses.factures),
}
OPERATIONS = {"payer_facture": "paiement", "faire_virement": "virement"}
SALUTATIONS = {"salam", "slm", "salam 3likom", "salam alaykom", "سلام", "السلام عليكم"}
# Accusés de réception et remerciements : ni une demande, ni du hors-sujet.
POLITESSES = {
    "mzyan", "mzn", "mzyane", "مزيان", "merci", "merci bcp", "merci beaucoup", "chokran", "choukran", "شكرا",
    "ok", "okay", "d'accord", "dacc", "safi", "tres bien", "très bien", "top", "barak allah fik", "lah yjazik bikhir",
}  # fmt: skip
# Réponses à « Wach nconfirmi ? ». Liste fermée, lue par le code : le LLM ne décide jamais d'une confirmation.
OUI = {"oui", "oui, confirmer", "ah", "iyeh", "iyyeh", "wakha", "yes", "ok", "confirmer", "نعم", "اه", "واخا"}
NON = {"non", "non, annuler", "la", "lla", "no", "annuler", "لا"}

# Le LLM est créé au premier message, avec les outils que le serveur MCP annonce (tools/list).
llm = None


def le_llm():
    global llm
    if llm is None:
        llm = ChatOllama(
            model=os.environ.get("WAKIL_MODELE", "qwen3:4b-instruct"),
            temperature=0,
            num_predict=100,  # assez pour un appel d'outil ; son texte libre ne nous sert pas
        ).bind_tools(outils.descriptions_pour_le_llm(set(OUTILS), set(OPERATIONS)))
    return llm


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
    # Ce qu'est devenue l'opération, pour que le front mette la carte à jour.
    issue: Literal["faite", "annulee", "incomprise", "refusee", "erreur"] | None
    erreur: bool
    reponse: str


def nouveau_tour(demande: str, client_id: int, facture_id: int | None = None) -> dict:
    """Entrée d'un nouveau message. Sans cette remise à zéro, la mémoire garderait l'erreur ou l'outil du message précédent.

    facture_id : le client a cliqué « Payer avec Wakil » sur une facture précise. L'intention est sûre : on ne la fait
    pas deviner au LLM, on va droit à la vérification à blanc (et à la confirmation, toujours obligatoire).
    """
    tour = {
        "client_id": client_id,
        "messages": [HumanMessage(demande)],
        "demande": demande,
        "outil": None,
        "arguments": {},
        "resultat": None,
        "operation": None,
        "confirmation": None,
        "issue": None,
        "erreur": False,
        "reponse": "",
    }
    if facture_id is not None:
        tour |= {"outil": "payer_facture", "arguments": {"facture_id": facture_id}}
    return tour


def config(client_id: int, conversation_id: str) -> dict:
    """Le fil de conversation est rangé sous l'id du client : un autre client ne peut pas le relire, même en devinant l'id."""
    return {"configurable": {"thread_id": f"{client_id}:{conversation_id}"}}


def carte_en_attente(graphe, conf: dict) -> str | None:
    """L'identifiant de la carte « Wach nconfirmi ? » qui attend une réponse, s'il y en a une."""
    interruptions = graphe.get_state(conf).interrupts
    return interruptions[0].id if interruptions else None


def prochaine_entree(graphe, demande: str, client_id: int, conf: dict, facture_id: int | None = None) -> dict | Command:
    """Si une opération attend « Wach nconfirmi ? », le message du client est sa réponse : on reprend le graphe là où
    il s'était arrêté (Command(resume=…)). Sinon, c'est une nouvelle demande.

    Un clic sur « Payer avec Wakil » est toujours une nouvelle demande : la carte en attente, s'il y en a une, est
    abandonnée (LangGraph repart du début avec la nouvelle entrée)."""
    if facture_id is None and carte_en_attente(graphe, conf):
        return Command(resume=demande)
    return nouveau_tour(demande, client_id, facture_id)


def dire(texte: str) -> dict:
    """La réponse de Wakil, ajoutée aussi à l'historique pour les messages suivants."""
    return {"reponse": texte, "messages": [AIMessage(texte)]}


def simplifier(texte: str) -> str:
    """« Fatima », « fatima » et « Fâtima » se valent : minuscules, sans accents, sans ponctuation autour."""
    sans_accents = "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
    return sans_accents.lower().strip().strip("!?.,;:، ")


def avant_comprendre(etat: Etat) -> Literal["preparer_operation", "saluer", "remercier", "comprendre"]:
    """Aiguillage de départ : un bouton « Payer avec Wakil », une salutation ou une politesse ne passent pas par le LLM."""
    if etat.get("outil") in OPERATIONS:
        return "preparer_operation"
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
    message = le_llm().invoke([SystemMessage(SYSTEME), *etat["messages"][-HISTORIQUE:]])
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
    """Le code appelle l'outil (serveur MCP) pour le client de la session."""
    appeler, _ = OUTILS[etat["outil"]]
    try:
        return {"resultat": appeler(etat["client_id"])}
    except outils.OutilsIndisponibles:
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
    """Demande au serveur MCP une vérification à blanc : il retrouve la facture ou le bénéficiaire, et la banque
    vérifie ses règles sans rien exécuter (l'appel ne porte pas la confirmation du client).

    Le résultat devient la carte « Wach nconfirmi ? ». Si quelque chose manque ou si la banque refuse déjà (solde,
    plafond…), Wakil le dit tout de suite au lieu de faire confirmer une opération vouée à l'échec.
    """
    type_operation = OPERATIONS[etat["outil"]]
    try:
        apercu = outils.appeler(etat["client_id"], etat["outil"], etat.get("arguments") or {})
    except outils.RefusOutil as refus:
        return dire(reponses.refus(type_operation, refus.detail))
    except outils.OutilsIndisponibles:
        return {"erreur": True, **dire(reponses.ERREUR)}

    operation = {"type": type_operation, **apercu}
    operation |= {
        "intro": reponses.INTRO[type_operation],
        "question": reponses.QUESTION[type_operation],
        "texte": reponses.confirmation(operation),  # le tout en une phrase : historique du LLM, terminal
    }
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
    """Le client a dit oui : l'appel porte sa confirmation, la banque exécute pour de vrai et revérifie ses règles.

    On renvoie les identifiants exacts de la carte (facture, bénéficiaire) : c'est bien l'opération affichée qui part.
    """
    operation, client_id = etat["operation"], etat["client_id"]
    # À la reprise, la case « comprendre » n'est pas rejouée : on redonne l'outil pour l'événement envoyé au front.
    outil = {"outil": etat["outil"]}
    if operation["type"] == "paiement":
        arguments = {"facture_id": operation["facture_id"]}
    else:
        arguments = {"beneficiaire_id": operation["beneficiaire_id"], "montant": operation["montant"]}
    try:
        resultat = outils.appeler(client_id, etat["outil"], arguments, confirme=True)
    except outils.RefusOutil as refus:  # la situation a changé entre la carte et le « oui »
        return {**outil, "issue": "refusee", **dire(reponses.refus(operation["type"], refus.detail))}
    except outils.OutilsIndisponibles:
        return {**outil, "issue": "erreur", "erreur": True, **dire(reponses.ERREUR_OPERATION)}
    return {
        **outil,
        "issue": "faite",
        "resultat": resultat,
        **dire(reponses.operation_faite(operation["type"], resultat)),
    }


def annuler(etat: Etat) -> dict:
    """« La », ou une réponse qui n'est ni oui ni non : on ne touche à rien."""
    outil = {"outil": etat["outil"]}
    if etat.get("confirmation") == "non":
        return {**outil, "issue": "annulee", **dire(reponses.ANNULEE[etat["operation"]["type"]])}
    return {**outil, "issue": "incomprise", **dire(reponses.CONFIRMATION_INCOMPRISE)}


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
