"""Tests des routes des comptes."""

from datetime import datetime

SALMA = {"X-Client-Id": "1"}
YOUSSEF = {"X-Client-Id": "2"}


def test_solde_de_son_propre_compte(api):
    reponse = api.get("/comptes/1/solde", headers=SALMA)
    assert reponse.status_code == 200
    assert reponse.json() == {"compte_id": 1, "solde": "2350.00", "devise": "DH"}


def test_solde_du_compte_d_un_autre_client_est_introuvable(api):
    reponse = api.get("/comptes/1/solde", headers=YOUSSEF)
    assert reponse.status_code == 404


def test_solde_sans_client_connecte_est_refuse(api):
    reponse = api.get("/comptes/1/solde")
    assert reponse.status_code == 422  # en-tête X-Client-Id manquant


def test_transactions_les_plus_recentes_d_abord(api):
    reponse = api.get("/comptes/1/transactions", headers=SALMA)
    assert reponse.status_code == 200
    dates = [datetime.fromisoformat(t["date"]) for t in reponse.json()]
    assert len(dates) == 10  # limite par défaut
    assert dates == sorted(dates, reverse=True)


def test_transactions_avec_une_limite(api):
    reponse = api.get("/comptes/1/transactions?limite=3", headers=SALMA)
    assert len(reponse.json()) == 3


def test_transactions_limite_trop_grande_refusee(api):
    reponse = api.get("/comptes/1/transactions?limite=100", headers=SALMA)
    assert reponse.status_code == 422


def test_transactions_du_compte_d_un_autre_client_introuvables(api):
    reponse = api.get("/comptes/1/transactions", headers=YOUSSEF)
    assert reponse.status_code == 404
