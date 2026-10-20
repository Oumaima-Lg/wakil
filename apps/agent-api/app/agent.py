"""Le graphe de Wakil : le LLM choisit l'outil, le code appelle la banque et écrit la réponse."""

import os
from typing import Annotated, Literal, TypedDict

import httpx
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app import banque, reponses

SYSTEME = (
    "Tu es Wakil, l'assistant de la Banque Atlas Démo (banque fictive). "
    "Le client écrit en darija marocaine, en lettres arabes ou latines, souvent mélangée au français. "
    "Si la demande concerne son compte, appelle l'outil adapté. "
    "Sinon, réponds en darija que tu ne t'occupes que de la banque."
)


def description(nom: str, texte: str) -> dict:
    """Ce que le LLM voit d'un outil : un nom et une description, sans aucun paramètre (surtout pas le client_id)."""
    return {
        "type": "function",
        "function": {"name": nom, "description": texte, "parameters": {"type": "object", "properties": {}}},
    }


# Liste fermée : le LLM ne peut choisir que parmi ces outils, tous en lecture seule.
OUTILS = {
    "consulter_solde": (banque.solde, reponses.solde),
    "lister_transactions": (banque.transactions, reponses.transactions),
    "lister_factures": (banque.factures_impayees, reponses.factures),
}
DESCRIPTIONS = [
    description("consulter_solde", "Donne le solde actuel du compte du client."),
    description(
        "lister_transactions", "Liste les dernières opérations du compte du client (dépenses, virements reçus)."
    ),
    description("lister_factures", "Liste les factures impayées du client (eau, électricité, internet, mobile)."),
]
SALUTATIONS = {"salam", "slm", "salam 3likom", "salam alaykom", "سلام", "السلام عليكم"}
# Accusés de réception et remerciements : ni une demande, ni du hors-sujet.
POLITESSES = {
    "mzyan", "mzn", "mzyane", "مزيان", "merci", "merci bcp", "merci beaucoup", "chokran", "choukran", "شكرا",
    "ok", "okay", "d'accord", "dacc", "safi", "tres bien", "très bien", "top", "barak allah fik", "lah yjazik bikhir",
}  # fmt: skip

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
    resultat: dict | list | None
    erreur: bool
    reponse: str


def nouveau_tour(demande: str, client_id: int) -> dict:
    """Entrée d'un nouveau message. Sans cette remise à zéro, la mémoire garderait l'erreur ou l'outil du message précédent."""
    return {
        "client_id": client_id,
        "messages": [HumanMessage(demande)],
        "demande": demande,
        "outil": None,
        "resultat": None,
        "erreur": False,
        "reponse": "",
    }


def config(client_id: int, conversation_id: str) -> dict:
    """Le fil de conversation est rangé sous l'id du client : un autre client ne peut pas le relire, même en devinant l'id."""
    return {"configurable": {"thread_id": f"{client_id}:{conversation_id}"}}


def dire(texte: str) -> dict:
    """La réponse de Wakil, ajoutée aussi à l'historique pour les messages suivants."""
    return {"reponse": texte, "messages": [AIMessage(texte)]}


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
    """Le LLM lit la demande, avec les derniers messages pour le contexte, et choisit un outil ou aucun."""
    message = llm.invoke([SystemMessage(SYSTEME), *etat["messages"][-HISTORIQUE:]])
    nom = message.tool_calls[0]["name"] if message.tool_calls else None
    # Un nom d'outil inventé par le LLM est traité comme « aucun outil ».
    return {"outil": nom if nom in OUTILS else None}


def apres_comprendre(etat: Etat) -> Literal["executer_outil", "refuser"]:
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


graphe = StateGraph(Etat)
graphe.add_node("saluer", saluer)
graphe.add_node("remercier", remercier)
graphe.add_node("comprendre", comprendre)
graphe.add_node("executer_outil", executer_outil)
graphe.add_node("repondre", repondre)
graphe.add_node("refuser", refuser)
graphe.add_conditional_edges(START, avant_comprendre)
graphe.add_conditional_edges("comprendre", apres_comprendre)
graphe.add_edge("executer_outil", "repondre")
graphe.add_edge("saluer", END)
graphe.add_edge("remercier", END)
graphe.add_edge("repondre", END)
graphe.add_edge("refuser", END)
# Le checkpointer sauvegarde l'état après chaque case (en mémoire vive ; dans PostgreSQL à l'étape S3).
wakil = graphe.compile(checkpointer=InMemorySaver())
