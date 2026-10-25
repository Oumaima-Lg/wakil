"""Tests de la route des virements."""

from decimal import Decimal

import pytest

SALMA = {"X-Client-Id": "1"}
YOUSSEF = {"X-Client-Id": "2"}
NADIA = {"X-Client-Id": "3"}


def nombre_d_audits(conn):
    return conn.execute("SELECT count(*) AS n FROM audit").fetchone()["n"]


def premier_beneficiaire(conn, client_id):
    """Premier bénéficiaire du client, avec le compte et le solde qu'il a dans la banque."""
    return conn.execute(
        "SELECT b.id, c.id AS compte_id, c.solde FROM beneficiaires b JOIN comptes c ON c.rib = b.rib"
        " WHERE b.client_id = %s ORDER BY b.id LIMIT 1",
        (client_id,),
    ).fetchone()


def test_virement_debite_l_emetteur_et_credite_le_beneficiaire(api, conn):
    beneficiaire = premier_beneficiaire(conn, 1)

    reponse = api.post("/virements", headers=SALMA, json={"beneficiaire_id": beneficiaire["id"], "montant": "500"})

    assert reponse.status_code == 200
    assert reponse.json()["nouveau_solde"] == "1850.00"  # 2 350 - 500
    assert reponse.json()["simulation"] is False
    solde_beneficiaire = conn.execute(
        "SELECT solde FROM comptes WHERE id = %s", (beneficiaire["compte_id"],)
    ).fetchone()["solde"]
    assert solde_beneficiaire == beneficiaire["solde"] + Decimal("500")
    recu = conn.execute(
        "SELECT montant, libelle FROM transactions WHERE compte_id = %s ORDER BY id DESC LIMIT 1",
        (beneficiaire["compte_id"],),
    ).fetchone()
    assert (recu["montant"], recu["libelle"]) == (Decimal("500.00"), "Virement reçu de Salma Alaoui")
    audit = conn.execute("SELECT action FROM audit WHERE client_id = 1 ORDER BY id DESC LIMIT 1").fetchone()
    assert audit["action"] == "virement"


def test_virement_au_dessus_du_plafond_refuse(api, conn):
    beneficiaire = premier_beneficiaire(conn, 3)  # Nadia : 18 500 DH, plafond de 2 000 DH

    reponse = api.post("/virements", headers=NADIA, json={"beneficiaire_id": beneficiaire["id"], "montant": "3000"})

    assert reponse.status_code == 409
    assert reponse.json()["detail"] == {
        "code": "plafond_depasse",
        "message": "Plafond de virement dépassé",
        "plafond": "2000.00",
        "montant": "3000.00",
    }
    assert api.get("/comptes/3/solde", headers=NADIA).json()["solde"] == "18500.00"


def test_virement_sans_solde_suffisant_refuse(api, conn):
    beneficiaire = premier_beneficiaire(conn, 2)  # Youssef : 150 DH

    reponse = api.post("/virements", headers=YOUSSEF, json={"beneficiaire_id": beneficiaire["id"], "montant": "500"})

    assert reponse.status_code == 409
    assert reponse.json()["detail"] == {
        "code": "solde_insuffisant",
        "message": "Solde insuffisant",
        "solde": "150.00",
        "montant": "500.00",
    }


def test_virement_vers_le_beneficiaire_d_un_autre_client_refuse(api, conn):
    beneficiaire_de_salma = premier_beneficiaire(conn, 1)

    reponse = api.post(
        "/virements", headers=YOUSSEF, json={"beneficiaire_id": beneficiaire_de_salma["id"], "montant": "10"}
    )

    assert reponse.status_code == 404


@pytest.mark.parametrize("montant", ["0", "-50", "10.123"])
def test_virement_avec_un_montant_invalide_refuse(api, conn, montant):
    beneficiaire = premier_beneficiaire(conn, 1)

    reponse = api.post("/virements", headers=SALMA, json={"beneficiaire_id": beneficiaire["id"], "montant": montant})

    assert reponse.status_code == 422


def test_simuler_un_virement_ne_change_rien(api, conn):
    beneficiaire = premier_beneficiaire(conn, 1)
    audits_avant = nombre_d_audits(conn)

    reponse = api.post(
        "/virements?simulation=true", headers=SALMA, json={"beneficiaire_id": beneficiaire["id"], "montant": "500"}
    )

    assert reponse.status_code == 200
    resultat = reponse.json()
    assert (resultat["montant"], resultat["nouveau_solde"], resultat["simulation"]) == ("500.00", "1850.00", True)
    assert resultat["beneficiaire_rib_masque"].startswith("•••• ") and len(resultat["beneficiaire_rib_masque"]) == 9
    assert api.get("/comptes/1/solde", headers=SALMA).json()["solde"] == "2350.00"
    solde_beneficiaire = conn.execute(
        "SELECT solde FROM comptes WHERE id = %s", (beneficiaire["compte_id"],)
    ).fetchone()["solde"]
    assert solde_beneficiaire == beneficiaire["solde"]
    assert nombre_d_audits(conn) == audits_avant


def test_simuler_un_virement_au_dessus_du_plafond_donne_le_refus(api, conn):
    beneficiaire = premier_beneficiaire(conn, 3)

    reponse = api.post(
        "/virements?simulation=true", headers=NADIA, json={"beneficiaire_id": beneficiaire["id"], "montant": "3000"}
    )

    assert reponse.status_code == 409
    assert reponse.json()["detail"]["code"] == "plafond_depasse"
