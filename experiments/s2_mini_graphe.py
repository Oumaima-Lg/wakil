# /// script
# requires-python = ">=3.12"
# dependencies = ["langgraph"]
# ///
"""S2, morceau 1 : le script S0 réécrit en graphe LangGraph.

Lancer : uv run experiments/s2_mini_graphe.py
Le LLM choisit l'outil ; le code exécute l'outil et écrit la réponse.
"""

import json
import urllib.request
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

URL = "http://localhost:11434/v1/chat/completions"
MODELE = "qwen3:4b-instruct"
SYSTEME = (
    "Tu es Wakil, l'assistant de la Banque Atlas Démo (banque fictive). "
    "Le client écrit en darija marocaine, en lettres arabes ou latines, souvent mélangée au français. "
    "Si la demande concerne son compte, appelle l'outil adapté. "
    "Sinon, réponds en darija que tu ne t'occupes que de la banque."
)


def outil(nom, description):
    parametres = {"type": "object", "properties": {}}
    return {"type": "function", "function": {"name": nom, "description": description, "parameters": parametres}}


OUTILS = [
    outil("consulter_solde", "Donne le solde actuel du compte du client."),
    outil("lister_transactions", "Liste les dernières opérations du compte du client (dépenses, virements reçus)."),
    outil("lister_factures", "Liste les factures impayées du client (eau, électricité, internet, mobile)."),
]

# Fausse banque : au morceau 2, ces fonctions appelleront bank-api.
FAUSSE_BANQUE = {
    "consulter_solde": lambda: {"solde": "2 350"},
    "lister_transactions": lambda: {"nombre": 20},
    "lister_factures": lambda: {"impayees": 2, "total": "561"},
}
# Les phrases sont écrites par nous : aucun chiffre n'est rédigé par le LLM.
PHRASES = {
    "consulter_solde": "Solde dyalek howa {solde} DH.",
    "lister_transactions": "Lqit {nombre} opérations f compte dyalek.",
    "lister_factures": "3ndek {impayees} factures mazal ma tkhelsou ({total} DH).",
}


# L'état : la « mémoire » partagée que chaque nœud lit et complète.
class Etat(TypedDict, total=False):
    demande: str  # ce que le client a écrit
    outil: str | None  # choisi par le LLM (None : aucun outil)
    resultat: dict  # renvoyé par la banque
    reponse: str  # ce que Wakil répond


def comprendre(etat: Etat) -> dict:
    """Nœud 1 : le LLM lit la demande et choisit un outil, ou aucun."""
    corps = {
        "model": MODELE,
        "temperature": 0,
        "max_tokens": 100,  # assez pour un appel d'outil ; son texte libre ne nous sert pas
        "tools": OUTILS,
        "messages": [{"role": "system", "content": SYSTEME}, {"role": "user", "content": etat["demande"]}],
    }
    requete = urllib.request.Request(URL, data=json.dumps(corps).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(requete, timeout=300) as reponse:
        message = json.load(reponse)["choices"][0]["message"]
    appels = message.get("tool_calls")
    return {"outil": appels[0]["function"]["name"] if appels else None}


def executer_outil(etat: Etat) -> dict:
    """Nœud 2 : le code exécute l'outil choisi."""
    return {"resultat": FAUSSE_BANQUE[etat["outil"]]()}


def repondre(etat: Etat) -> dict:
    """Nœud 3 : le code remplit la phrase avec le résultat de la banque."""
    return {"reponse": PHRASES[etat["outil"]].format(**etat["resultat"])}


def refuser(etat: Etat) -> dict:
    """Nœud 4 : demande hors sujet, message fixe (le modèle ne peut pas partir en boucle)."""
    return {"reponse": "Smeh lia, ana ghir l'assistant dyal Banque Atlas Démo."}


def apres_comprendre(etat: Etat) -> Literal["executer_outil", "refuser"]:
    """Aiguillage : choisit la case suivante selon la décision du LLM."""
    return "executer_outil" if etat["outil"] else "refuser"


# Le graphe : les cases (nœuds) et les flèches (arêtes).
graphe = StateGraph(Etat)
graphe.add_node("comprendre", comprendre)
graphe.add_node("executer_outil", executer_outil)
graphe.add_node("repondre", repondre)
graphe.add_node("refuser", refuser)
graphe.add_edge(START, "comprendre")
graphe.add_conditional_edges("comprendre", apres_comprendre)
graphe.add_edge("executer_outil", "repondre")
graphe.add_edge("repondre", END)
graphe.add_edge("refuser", END)
wakil = graphe.compile()

DEMANDES = [
    "chhal bqa f compte dyali ?",
    "واش عندي شي فاتورة ما خلصتهاش؟",
    "3tini la liste dyal les transactions dyali",
    "kifach ndir tajine b l7em ?",
]
for demande in DEMANDES:
    print(f"Client : {demande}")
    # stream affiche chaque case traversée et ce qu'elle a ajouté à l'état.
    for etape in wakil.stream({"demande": demande}, stream_mode="updates"):
        for noeud, ajout in etape.items():
            print(f"   [{noeud}] {ajout}")
    print()
