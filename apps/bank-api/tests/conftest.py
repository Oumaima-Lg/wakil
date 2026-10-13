"""Préparation commune des tests. Équivalent Spring : @SpringBootTest + MockMvc.

Les tests utilisent la base locale remplie par data/seed/generer_donnees.py (graine fixe) :
Salma (client 1, compte 1) a 2 350 DH, Youssef (client 2, compte 2) a 150 DH,
Nadia (client 3, compte 3) a 18 500 DH et un plafond de virement de 2 000 DH.
"""

import pytest
from fastapi.testclient import TestClient

from app.db import get_conn, pool
from app.main import app


@pytest.fixture(scope="session")
def client_http():
    """Client HTTP de test : appelle l'API sans lancer de vrai serveur."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def conn(client_http):
    """Connexion partagée par l'API et le test, dans une transaction annulée à la fin du test.

    Comme @Transactional sur un test Spring : paiements et virements ne modifient jamais la vraie base.
    """
    with pool.connection() as connexion, connexion.transaction(force_rollback=True):
        app.dependency_overrides[get_conn] = lambda: connexion
        yield connexion
        app.dependency_overrides.clear()


@pytest.fixture
def api(client_http, conn):
    return client_http
