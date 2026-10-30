"""Doublures communes : les tests tournent sans Ollama ni serveur MCP (comme des mocks Mockito)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app import agent
from app.main import app
from app.session import COOKIE
from tests.jetons import CLE_PUBLIQUE, jeton


@pytest.fixture(autouse=True)
def cle_de_test(monkeypatch):
    """La clé publique d'une paire de test : la vraie reste dans .env."""
    monkeypatch.setenv("WAKIL_JWT_CLE_PUBLIQUE", CLE_PUBLIQUE)


@pytest.fixture
def api():
    """Un client HTTP neuf pour chaque test : ses cookies ne passent pas d'un test à l'autre."""
    return TestClient(app)


@pytest.fixture
def salma(api):
    """Un client HTTP déjà connecté en tant que Salma : le cookie que portail-api aurait posé."""
    api.cookies.set(COOKIE, jeton(1))
    return api


@pytest.fixture
def connecter():
    """Connecte un client de démo dans un client HTTP neuf : chacun garde ses propres cookies."""

    def ouvrir(client_id):
        http = TestClient(app)
        http.cookies.set(COOKIE, jeton(client_id))
        return http

    return ouvrir


class FauxLLM:
    """Doublure du LLM : choisit toujours le même outil (avec ses paramètres), ou plusieurs (une liste de noms), et
    garde les messages reçus."""

    def __init__(self, outil=None, arguments=None):
        self.outil = outil
        self.arguments = arguments or {}
        self.recus = []

    @property
    def appels(self):
        return len(self.recus)

    def invoke(self, messages):
        self.recus.append(messages)
        noms = self.outil if isinstance(self.outil, list) else [self.outil] if self.outil else []
        appels_outil = [{"name": nom, "args": self.arguments, "id": str(i)} for i, nom in enumerate(noms)]
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
