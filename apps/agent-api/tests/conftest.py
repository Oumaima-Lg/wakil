"""Doublures communes : les tests tournent sans Ollama ni bank-api (comme des mocks Mockito)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app import agent, banque
from app.main import app

PROFILS = {
    1: ("madame", "Salma", "Alaoui", "Casablanca"),
    2: ("monsieur", "Youssef", "Berrada", "Rabat"),
    3: ("madame", "Nadia", "Tazi", "Marrakech"),
}


@pytest.fixture(autouse=True)
def cle_de_test(monkeypatch):
    """Une clé de signature de test : la vraie reste dans .env."""
    monkeypatch.setenv("WAKIL_JWT_SECRET", "cle-de-test-de-wakil-assez-longue-pour-hs256")


@pytest.fixture(autouse=True)
def fausse_banque(monkeypatch):
    """bank-api ne tourne pas pendant les tests : profil, compte et factures des clients de démo sont simulés."""

    def profil(client_id):
        civilite, prenom, nom, ville = PROFILS[client_id]
        return {"id": client_id, "civilite": civilite, "prenom": prenom, "nom": nom, "ville": ville}

    def compte(client_id):
        return {"id": client_id, "rib_masque": "•••• 9114", "plafond_virement": "10000.00", "solde": "2350.00"}

    monkeypatch.setattr(banque, "profil", profil)
    monkeypatch.setattr(banque, "compte", compte)
    monkeypatch.setattr(banque, "factures_impayees", lambda client_id: [{"montant": "312.00"}, {"montant": "249.00"}])
    monkeypatch.setattr(
        banque,
        "operations",
        lambda client_id: [{"id": 1, "date": "2026-10-21T09:00:00Z", "montant": "-57.98", "libelle": "Café"}],
    )
    monkeypatch.setattr(
        banque,
        "toutes_factures",
        lambda client_id: [
            {"id": 1, "fournisseur": "Eau & Électricité (démo)", "montant": "312.00", "statut": "impayee"}
        ],
    )
    monkeypatch.setattr(
        banque,
        "beneficiaires",
        lambda client_id: [{"id": 1, "nom": "Fatima Lahlou", "rib_masque": "•••• 8633", "interne": True}],
    )


@pytest.fixture
def api():
    """Un client HTTP neuf pour chaque test : ses cookies ne passent pas d'un test à l'autre."""
    return TestClient(app)


@pytest.fixture
def salma(api):
    """Un client HTTP déjà connecté en tant que Salma (le cookie de session est posé)."""
    api.post("/session", json={"client_id": 1})
    return api


@pytest.fixture
def connecter():
    """Ouvre la session d'un client de démo dans un client HTTP neuf : chacun garde ses propres cookies."""

    def ouvrir(client_id):
        http = TestClient(app)
        http.post("/session", json={"client_id": client_id})
        return http

    return ouvrir


class FauxLLM:
    """Doublure du LLM : choisit toujours le même outil (avec ses paramètres) et garde les messages reçus."""

    def __init__(self, outil=None, arguments=None):
        self.outil = outil
        self.arguments = arguments or {}
        self.recus = []

    @property
    def appels(self):
        return len(self.recus)

    def invoke(self, messages):
        self.recus.append(messages)
        appels_outil = [{"name": self.outil, "args": self.arguments, "id": "1"}] if self.outil else []
        return AIMessage(content="", tool_calls=appels_outil)


@pytest.fixture
def faux_llm(monkeypatch):
    """Remplace le LLM par une doublure qui choisit l'outil donné."""

    def installer(outil=None, arguments=None):
        faux = FauxLLM(outil, arguments)
        monkeypatch.setattr(agent, "llm", faux)
        return faux

    return installer


@pytest.fixture
def tour():
    """Envoie un message à Wakil, dans une conversation neuve propre à ce test (la mémoire ne déborde pas)."""
    conversation = str(uuid.uuid4())

    def envoyer(texte, client_id=1, conversation_id=conversation):
        return agent.wakil.invoke(agent.nouveau_tour(texte, client_id), agent.config(client_id, conversation_id))

    return envoyer
