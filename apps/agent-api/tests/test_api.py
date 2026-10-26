"""Tests de la route /chat (flux SSE), sans Ollama ni bank-api."""

import time
import uuid

import httpx
import pytest
from langchain_core.messages import AIMessage

from app import agent, main, reponses
from tests.sse import evenements


def test_chat_envoie_les_etapes_puis_la_reponse(salma, faux_llm, monkeypatch):
    faux_llm("consulter_solde")
    monkeypatch.setitem(agent.OUTILS, "consulter_solde", (lambda client_id: {"solde": "2350.00"}, reponses.solde))

    reponse = salma.post("/chat", json={"conversation_id": str(uuid.uuid4()), "texte": "chhal bqa f compte dyali ?"})

    assert reponse.headers["content-type"].startswith("text/event-stream")
    assert evenements(reponse) == [
        ("etape", {"noeud": "comprendre", "outil": "consulter_solde"}),
        ("etape", {"noeud": "executer_outil", "outil": None}),  # le résultat brut de la banque ne part pas ici…
        (  # … mais seulement avec la réponse, pour que le front affiche le solde en grand
            "reponse",
            {
                "texte": "Solde dyalek howa 2 350 DH.",
                "outil": "consulter_solde",
                "donnees": {"solde": "2350.00"},
                "erreur": False,
            },
        ),
        ("fin", {}),
    ]


def test_un_salut_repond_sans_outil_ni_donnees(salma, faux_llm):
    faux_llm()

    reponse = salma.post("/chat", json={"conversation_id": str(uuid.uuid4()), "texte": "salam"})

    assert evenements(reponse) == [
        ("reponse", {"texte": reponses.SALUT, "outil": None, "donnees": None, "erreur": False}),
        ("fin", {}),
    ]


def test_banque_injoignable_la_reponse_le_signale(salma, faux_llm, monkeypatch):
    faux_llm("consulter_solde")

    def banque_en_panne(client_id):
        raise httpx.ConnectError("bank-api ne répond pas")

    monkeypatch.setitem(agent.OUTILS, "consulter_solde", (banque_en_panne, reponses.solde))

    reponse = salma.post("/chat", json={"conversation_id": str(uuid.uuid4()), "texte": "chhal f compte dyali ?"})

    assert evenements(reponse)[-2] == (
        "reponse",
        {"texte": reponses.ERREUR, "outil": "consulter_solde", "donnees": None, "erreur": True},
    )


def test_llm_en_panne_le_flux_se_termine_proprement(salma, monkeypatch):
    class LLMEnPanne:
        def invoke(self, messages):
            raise httpx.ConnectError("Ollama ne répond pas")

    monkeypatch.setattr(agent, "llm", LLMEnPanne())

    reponse = salma.post("/chat", json={"conversation_id": str(uuid.uuid4()), "texte": "chhal f compte dyali ?"})

    assert reponse.status_code == 200  # le flux avait déjà commencé
    assert evenements(reponse) == [("erreur", {"texte": reponses.PANNE}), ("fin", {})]


def test_un_llm_lent_ne_laisse_pas_la_connexion_muette(salma, monkeypatch):
    """Modèle froid : pendant que le LLM réfléchit, des battements partent pour que le proxy ne coupe pas."""

    class LLMLent:
        def invoke(self, messages):
            time.sleep(0.3)
            return AIMessage(content="", tool_calls=[{"name": "consulter_solde", "args": {}, "id": "1"}])

    monkeypatch.setattr(agent, "llm", LLMLent())
    monkeypatch.setattr(main, "BATTEMENT", 0.05)  # 50 ms au lieu de 10 s, pour que le test reste rapide
    monkeypatch.setitem(agent.OUTILS, "consulter_solde", (lambda client_id: {"solde": "2350.00"}, reponses.solde))

    reponse = salma.post("/chat", json={"conversation_id": str(uuid.uuid4()), "texte": "chhal f compte dyali ?"})

    assert reponse.text.startswith(": battement\n\n")  # le premier octet part avant la réponse du LLM
    assert evenements(reponse)[-2][1]["texte"] == "Solde dyalek howa 2 350 DH."
    assert evenements(reponse)[-1] == ("fin", {})


@pytest.mark.parametrize(
    "corps",
    [
        {"conversation_id": "abc", "texte": "a" * 501},  # message trop long
        {"conversation_id": "abc", "texte": ""},  # message vide
        {"conversation_id": "../autre-client", "texte": "salam"},  # id de conversation invalide
    ],
)
def test_chat_message_invalide_refuse(salma, corps):
    assert salma.post("/chat", json=corps).status_code == 422
