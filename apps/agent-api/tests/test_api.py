"""Tests de la route /chat (flux SSE), sans Ollama ni bank-api."""

import json
import uuid

import httpx
import pytest

from app import agent, reponses


def evenements(reponse):
    """Découpe un flux SSE en liste de (nom de l'événement, données)."""
    resultat = []
    for bloc in reponse.text.strip().split("\n\n"):
        champs = dict(ligne.split(": ", 1) for ligne in bloc.splitlines())
        resultat.append((champs["event"], json.loads(champs["data"])))
    return resultat


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
