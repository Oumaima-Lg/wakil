"""Doublures communes : les tests tournent sans Ollama ni bank-api (comme des mocks Mockito)."""

import uuid

import pytest
from langchain_core.messages import AIMessage

from app import agent


class FauxLLM:
    """Doublure du LLM : choisit toujours le même outil et garde les messages reçus à chaque appel."""

    def __init__(self, outil=None):
        self.outil = outil
        self.recus = []

    @property
    def appels(self):
        return len(self.recus)

    def invoke(self, messages):
        self.recus.append(messages)
        appels_outil = [{"name": self.outil, "args": {}, "id": "1"}] if self.outil else []
        return AIMessage(content="", tool_calls=appels_outil)


@pytest.fixture
def faux_llm(monkeypatch):
    """Remplace le LLM par une doublure qui choisit l'outil donné."""

    def installer(outil=None):
        faux = FauxLLM(outil)
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
