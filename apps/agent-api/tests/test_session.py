"""Tests de la session vue par agent-api : chaque test essaie de tromper le jeton d'une façon différente.

agent-api ne crée aucun jeton (c'est portail-api) : il les vérifie avec la clé publique.
"""

import base64
import json
import uuid
from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives.asymmetric import rsa

from app import agent, reponses
from app.session import COOKIE
from tests.jetons import CLE_PUBLIQUE, jeton

MESSAGE = {"conversation_id": "essai", "texte": "chhal bqa f compte dyali ?"}


def b64(donnees: dict) -> str:
    """Encodage base64url d'une partie de JWT (sans le « = » final)."""
    return base64.urlsafe_b64encode(json.dumps(donnees).encode()).rstrip(b"=").decode()


def test_chat_sans_session_refuse(api):
    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_modifie_a_la_main_refuse(api):
    entete, _, signature = jeton(1).split(".")
    exp = int((datetime.now(UTC) + timedelta(minutes=30)).timestamp())
    contenu_falsifie = b64({"sub": "2", "iss": "portail-api", "aud": "agent-api", "exp": exp})
    api.cookies.set(COOKIE, f"{entete}.{contenu_falsifie}.{signature}")  # « je suis Youssef », sans la clé

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_signe_avec_une_autre_cle_refuse(api):
    cle_de_l_attaquant = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    api.cookies.set(COOKIE, jeton(2, cle=cle_de_l_attaquant))

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_hs256_signe_avec_la_cle_publique_refuse(api):
    """Attaque classique (« confusion d'algorithme ») : la clé publique n'est pas secrète. Un attaquant s'en sert comme
    mot de passe HS256 ; un serveur qui accepterait HS256 vérifierait avec cette même clé, et le jeton passerait."""
    api.cookies.set(COOKIE, jeton(2, cle=CLE_PUBLIQUE, algorithme="HS256"))

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_non_signe_alg_none_refuse(api):
    exp = int((datetime.now(UTC) + timedelta(minutes=30)).timestamp())
    contenu = {"sub": "2", "iss": "portail-api", "aud": "agent-api", "exp": exp}
    api.cookies.set(COOKIE, f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64(contenu)}.")

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_expire_refuse(api):
    api.cookies.set(COOKIE, jeton(1, exp=datetime.now(UTC) - timedelta(minutes=1)))

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_destine_a_un_autre_service_refuse(api):
    """Bien signé, mais destiné seulement à portail-api (« aud ») : agent-api le refuse."""
    api.cookies.set(COOKIE, jeton(1, aud="portail-api"))

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_d_un_autre_emetteur_refuse(api):
    api.cookies.set(COOKIE, jeton(1, iss="un-autre-service"))

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_sans_expiration_refuse(api):
    """Un jeton sans « exp » serait valable pour toujours : refusé."""
    api.cookies.set(COOKIE, jeton(1, exp=None))

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_l_en_tete_x_client_id_est_ignore(salma, faux_llm, monkeypatch):
    clients_appeles = []

    def fausse_banque(client_id, arguments=None):
        clients_appeles.append(client_id)
        return {"solde": "2350.00"}

    faux_llm("consulter_solde")
    monkeypatch.setitem(agent.OUTILS, "consulter_solde", (fausse_banque, reponses.solde))

    salma.post("/chat", headers={"X-Client-Id": "2"}, json={**MESSAGE, "conversation_id": str(uuid.uuid4())})

    assert clients_appeles == [1]  # c'est bien Salma (le jeton), pas Youssef (l'en-tête)


def test_les_routes_du_portail_ne_sont_pas_ici(salma):
    """La session et les pages sont servies par portail-api : agent-api n'a que /chat."""
    assert salma.post("/session", json={"client_id": 2}).status_code == 404
    assert salma.get("/moi/espace").status_code == 404
