"""Tests de la route /chat (flux SSE), sans Ollama ni bank-api."""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app import agent, reponses
from app.main import app

api = TestClient(app)
SALMA = {"X-Client-Id": "1"}


def evenements(reponse):
    """Découpe un flux SSE en liste de (nom de l'événement, données)."""
    resultat = []
    for bloc in reponse.text.strip().split("\n\n"):
        champs = dict(ligne.split(": ", 1) for ligne in bloc.splitlines())
        resultat.append((champs["event"], json.loads(champs["data"])))
    return resultat


def test_chat_envoie_les_etapes_puis_la_reponse(faux_llm, monkeypatch):
    faux_llm("consulter_solde")
    monkeypatch.setitem(agent.OUTILS, "consulter_solde", (lambda client_id: {"solde": "2350.00"}, reponses.solde))

    reponse = api.post(
        "/chat", headers=SALMA, json={"conversation_id": str(uuid.uuid4()), "texte": "chhal bqa f compte dyali ?"}
    )

    assert reponse.headers["content-type"].startswith("text/event-stream")
    assert evenements(reponse) == [
        ("etape", {"noeud": "comprendre", "outil": "consulter_solde"}),
        ("etape", {"noeud": "executer_outil", "outil": None}),  # le résultat brut de la banque ne part pas
        ("reponse", {"texte": "Solde dyalek howa 2 350 DH."}),
        ("fin", {}),
    ]


def test_chat_sans_client_connecte_refuse():
    reponse = api.post("/chat", json={"conversation_id": "abc", "texte": "salam"})
    assert reponse.status_code == 422


@pytest.mark.parametrize(
    "corps",
    [
        {"conversation_id": "abc", "texte": "a" * 501},  # message trop long
        {"conversation_id": "abc", "texte": ""},  # message vide
        {"conversation_id": "../autre-client", "texte": "salam"},  # id de conversation invalide
    ],
)
def test_chat_message_invalide_refuse(corps):
    assert api.post("/chat", headers=SALMA, json=corps).status_code == 422
