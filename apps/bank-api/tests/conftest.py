"""Préparation commune des tests. Équivalent Spring : @SpringBootTest + MockMvc.

Les tests utilisent la base locale remplie par data/seed/generer_donnees.py (graine fixe) :
Salma (client 1, compte 1) a 2 350 DH, Youssef (client 2, compte 2) a 150 DH,
Nadia (client 3, compte 3) a 18 500 DH et un plafond de virement de 2 000 DH.
"""

import base64
import os
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.db import get_conn, pool
from app.main import app


def nouvelle_cle() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def publique(cle: rsa.RSAPrivateKey) -> str:
    binaire = cle.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return base64.b64encode(binaire).decode()


# Les clés de test des deux émetteurs de confiance (jamais celles de .env) : bank-api ne reçoit que les publiques.
CLES = {"mcp-tools": nouvelle_cle(), "portail-api": nouvelle_cle()}
os.environ["MCP_JWT_CLE_PUBLIQUE"] = publique(CLES["mcp-tools"])
os.environ["WAKIL_JWT_CLE_PUBLIQUE"] = publique(CLES["portail-api"])


def jeton(client_id: int, emetteur: str = "mcp-tools", cle: rsa.RSAPrivateKey | None = None, **changements) -> str:
    """Un jeton comme ceux de mcp-tools ou de portail-api (10 minutes ici, pour ne pas expirer pendant les tests)."""
    maintenant = datetime.now(UTC)
    contenu = {
        "sub": str(client_id),
        "iss": emetteur,
        "aud": "bank-api",
        "iat": maintenant,
        "exp": maintenant + timedelta(minutes=10),
        **changements,
    }
    return jwt.encode(contenu, cle or CLES[emetteur], algorithm="RS256")


def entetes(client_id: int, **options) -> dict[str, str]:
    return {"Authorization": f"Bearer {jeton(client_id, **options)}"}


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


@pytest.fixture
def carte_neuve(conn):
    """Une seule carte, active, pour Salma, quoi qu'on ait fait dans la démo (blocage, opposition, remplacement) :
    remise à neuf dans la transaction du test, annulée à la fin. Les données de la démo ne sont pas touchées."""
    conn.execute("UPDATE cartes SET remplacee_par = NULL WHERE client_id = 1")
    conn.execute("DELETE FROM cartes WHERE client_id = 1")
    return conn.execute(
        "INSERT INTO cartes (client_id, compte_id, numero_masque, expiration)"
        " SELECT client_id, id, '•••• 7919', '02/29' FROM comptes WHERE client_id = 1 RETURNING id"
    ).fetchone()["id"]
