"""Tests de l'écran d'accueil et de l'espace bancaire."""

import httpx

from app import banque


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
    assert api.post("/session", json={"client_id": 1}).status_code == 503


def test_mon_espace_regroupe_tout_ce_que_le_front_affiche(salma):
    espace = salma.get("/moi/espace").json()

    assert set(espace) == {"profil", "compte", "operations", "factures", "beneficiaires"}
    assert espace["profil"]["prenom"] == "Salma"
    assert espace["compte"]["solde"] == "2350.00"


def test_mon_espace_sans_session_refuse(api):
    assert api.get("/moi/espace").status_code == 401
