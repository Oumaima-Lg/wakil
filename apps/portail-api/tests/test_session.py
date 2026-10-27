"""Tests de la session : le cookie, le jeton qu'il contient, et ce qu'on refuse."""

import base64
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives import serialization

from app.cles import generer
from app.session import COOKIE, creer_jeton


def test_ouvrir_une_session_pose_un_cookie_que_le_javascript_ne_peut_pas_lire(api):
    reponse = api.post("/session", json={"client_id": 1})

    assert reponse.json() == {"client_id": 1, "prenom": "Salma"}
    cookie = reponse.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE}=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


def test_le_jeton_se_verifie_avec_la_seule_cle_publique(api, cle_publique):
    """Ce que fait agent-api : il n'a que la clé publique, et cela suffit pour vérifier."""
    api.post("/session", json={"client_id": 1})

    contenu = jwt.decode(api.cookies[COOKIE], cle_publique, algorithms=["RS256"], audience="agent-api")

    assert (contenu["sub"], contenu["iss"]) == ("1", "portail-api")
    assert contenu["aud"] == ["portail-api", "agent-api"]
    assert jwt.get_unverified_header(api.cookies[COOKIE])["alg"] == "RS256"


def test_un_client_qui_n_est_pas_de_demo_est_refuse(api):
    assert api.post("/session", json={"client_id": 57}).status_code == 404


def test_moi_renvoie_le_profil_du_client_connecte(salma):
    assert salma.get("/moi").json()["prenom"] == "Salma"


def test_moi_sans_session_refuse(api):
    assert api.get("/moi").status_code == 401


def test_jeton_signe_avec_une_autre_cle_refuse(api):
    """Un attaquant qui fabrique sa propre paire de clés signe un jeton « je suis Youssef » : refusé."""
    cle_de_l_attaquant = serialization.load_der_private_key(base64.b64decode(generer()[0]), password=None)
    exp = datetime.now(UTC) + timedelta(minutes=30)
    faux = jwt.encode({"sub": "2", "iss": "portail-api", "aud": "portail-api", "exp": exp}, cle_de_l_attaquant, "RS256")
    api.cookies.set(COOKIE, faux)

    assert api.get("/moi").status_code == 401


def test_jeton_expire_refuse(api):
    api.cookies.set(COOKIE, creer_jeton(1, maintenant=datetime.now(UTC) - timedelta(minutes=31)))

    assert api.get("/moi").status_code == 401


def test_apres_deconnexion_moi_est_refuse(salma):
    assert salma.delete("/session").status_code == 204

    assert salma.get("/moi").status_code == 401
