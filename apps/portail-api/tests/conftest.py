"""Doublures communes : les tests tournent sans bank-api (comme des mocks Mockito), avec une paire de clés de test."""

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

from app import banque
from app.cles import generer
from app.main import app

PROFILS = {
    1: ("madame", "Salma", "Alaoui", "Casablanca"),
    2: ("monsieur", "Youssef", "Berrada", "Rabat"),
    3: ("madame", "Nadia", "Tazi", "Marrakech"),
}
CLE_PRIVEE, CLE_PUBLIQUE = generer()  # une paire tirée à chaque lancement des tests ; la vraie reste dans .env


@pytest.fixture(autouse=True)
def cle_de_test(monkeypatch):
    monkeypatch.setenv("WAKIL_JWT_CLE_PRIVEE", CLE_PRIVEE)


@pytest.fixture
def cle_publique():
    """La clé publique de la paire de test, celle qu'aurait agent-api."""
    return serialization.load_der_public_key(base64.b64decode(CLE_PUBLIQUE))


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
