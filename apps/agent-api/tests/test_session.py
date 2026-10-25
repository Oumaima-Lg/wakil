"""Tests de la session : chaque test essaie de tromper le jeton d'une façon différente."""

import base64
import json
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import jwt

from app import agent, banque, reponses
from app.session import COOKIE, creer_jeton

MESSAGE = {"conversation_id": "essai", "texte": "chhal bqa f compte dyali ?"}


def b64(donnees: dict) -> str:
    """Encodage base64url d'une partie de JWT (sans le « = » final)."""
    return base64.urlsafe_b64encode(json.dumps(donnees).encode()).rstrip(b"=").decode()


def test_les_clients_de_demo_sont_proposes_avec_un_resume_de_leur_compte(api):
    clients = api.get("/clients-demo").json()

    assert [c["prenom"] for c in clients] == ["Salma", "Youssef", "Nadia"]
    assert clients[0] == {
        "id": 1,
        "civilite": "madame",
        "prenom": "Salma",
        "nom": "Alaoui",
        "ville": "Casablanca",
        "scenario": "Cas normal",
        "solde": "2350.00",
        "plafond_virement": "10000.00",
        "factures_a_payer": 2,
        "total_a_payer": "561.00",
    }


def test_banque_injoignable_donne_une_erreur_503(api, monkeypatch):
    def banque_en_panne(client_id):
        raise httpx.ConnectError("bank-api ne répond pas")

    monkeypatch.setattr(banque, "profil", banque_en_panne)

    assert api.get("/clients-demo").status_code == 503


def test_moi_renvoie_le_profil_du_client_connecte(salma):
    assert salma.get("/moi").json()["prenom"] == "Salma"


def test_moi_sans_session_refuse(api):
    assert api.get("/moi").status_code == 401


def test_ouvrir_une_session_pose_un_cookie_que_le_javascript_ne_peut_pas_lire(api):
    reponse = api.post("/session", json={"client_id": 1})

    assert reponse.json() == {"client_id": 1, "prenom": "Salma"}
    cookie = reponse.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE}=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


def test_un_client_qui_n_est_pas_de_demo_est_refuse(api):
    assert api.post("/session", json={"client_id": 57}).status_code == 404


def test_chat_sans_session_refuse(api):
    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_modifie_a_la_main_refuse(api):
    entete, _, signature = creer_jeton(1).split(".")
    contenu_falsifie = b64({"sub": "2", "exp": int((datetime.now(UTC) + timedelta(minutes=30)).timestamp())})
    api.cookies.set(COOKIE, f"{entete}.{contenu_falsifie}.{signature}")  # « je suis Youssef », sans la clé

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_signe_avec_une_autre_cle_refuse(api):
    exp = datetime.now(UTC) + timedelta(minutes=30)
    api.cookies.set(COOKIE, jwt.encode({"sub": "2", "exp": exp}, "cle-inventee-par-un-attaquant-0123456789"))

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_non_signe_alg_none_refuse(api):
    exp = int((datetime.now(UTC) + timedelta(minutes=30)).timestamp())
    api.cookies.set(COOKIE, f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': '2', 'exp': exp})}.")

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_jeton_expire_refuse(api):
    il_y_a_31_minutes = datetime.now(UTC) - timedelta(minutes=31)
    api.cookies.set(COOKIE, creer_jeton(1, maintenant=il_y_a_31_minutes))

    assert api.post("/chat", json=MESSAGE).status_code == 401


def test_l_en_tete_x_client_id_est_ignore(salma, faux_llm, monkeypatch):
    clients_appeles = []

    def fausse_banque(client_id):
        clients_appeles.append(client_id)
        return {"solde": "2350.00"}

    faux_llm("consulter_solde")
    monkeypatch.setitem(agent.OUTILS, "consulter_solde", (fausse_banque, reponses.solde))

    salma.post("/chat", headers={"X-Client-Id": "2"}, json={**MESSAGE, "conversation_id": str(uuid.uuid4())})

    assert clients_appeles == [1]  # c'est bien Salma (le jeton), pas Youssef (l'en-tête)


def test_apres_deconnexion_le_chat_est_refuse(salma):
    assert salma.delete("/session").status_code == 204

    assert salma.post("/chat", json=MESSAGE).status_code == 401


def test_mon_espace_regroupe_tout_ce_que_le_front_affiche(salma):
    espace = salma.get("/moi/espace").json()

    assert set(espace) == {"profil", "compte", "operations", "factures", "beneficiaires"}
    assert espace["profil"]["prenom"] == "Salma"
    assert espace["compte"]["solde"] == "2350.00"


def test_mon_espace_sans_session_refuse(api):
    assert api.get("/moi/espace").status_code == 401
