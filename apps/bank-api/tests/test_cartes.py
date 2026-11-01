"""Tests des cartes : la liste, puis les changements d'état autorisés (et seulement eux)."""

import re

import pytest

SALMA = {"X-Client-Id": "1"}
YOUSSEF = {"X-Client-Id": "2"}


@pytest.fixture(autouse=True)
def salma_a_une_carte_neuve(carte_neuve):
    """Chaque test part d'une seule carte active pour Salma (voir carte_neuve dans conftest)."""


def carte_de(conn, client_id: int) -> int:
    return conn.execute("SELECT id FROM cartes WHERE client_id = %s ORDER BY id", (client_id,)).fetchone()["id"]


def statut(conn, carte_id: int) -> str:
    return conn.execute("SELECT statut FROM cartes WHERE id = %s", (carte_id,)).fetchone()["statut"]


def derniere_action(conn) -> str:
    return conn.execute("SELECT action FROM audit ORDER BY id DESC LIMIT 1").fetchone()["action"]


def test_le_client_voit_sa_carte_masquee(api):
    (carte,) = api.get("/clients/1/cartes", headers=SALMA).json()

    assert re.fullmatch(r"•••• \d{4}", carte["numero_masque"])  # jamais le numéro complet
    assert re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", carte["expiration"])
    assert (carte["statut"], carte["motif_opposition"]) == ("active", None)


def test_les_cartes_d_un_autre_client_sont_introuvables(api, conn):
    assert api.get("/clients/1/cartes", headers=YOUSSEF).status_code == 404
    assert api.post(f"/cartes/{carte_de(conn, 1)}/blocage", headers=YOUSSEF).status_code == 404


def test_bloquer_puis_debloquer(api, conn):
    carte = carte_de(conn, 1)

    assert api.post(f"/cartes/{carte}/blocage", headers=SALMA).json()["statut"] == "bloquee"
    assert derniere_action(conn) == "carte_bloquee"
    assert api.post(f"/cartes/{carte}/deblocage", headers=SALMA).json()["statut"] == "active"
    assert derniere_action(conn) == "carte_debloquee"


def test_bloquer_une_carte_deja_bloquee_est_refuse(api, conn):
    carte = carte_de(conn, 1)
    api.post(f"/cartes/{carte}/blocage", headers=SALMA)

    reponse = api.post(f"/cartes/{carte}/blocage", headers=SALMA)

    assert (reponse.status_code, reponse.json()["detail"]["code"]) == (409, "carte_deja_bloquee")


def test_debloquer_une_carte_active_est_refuse(api, conn):
    reponse = api.post(f"/cartes/{carte_de(conn, 1)}/deblocage", headers=SALMA)

    assert (reponse.status_code, reponse.json()["detail"]["code"]) == (409, "carte_deja_active")


def test_l_opposition_est_definitive(api, conn):
    carte = carte_de(conn, 1)

    opposee = api.post(f"/cartes/{carte}/opposition", headers=SALMA, json={"motif": "vol"}).json()

    assert (opposee["statut"], opposee["motif_opposition"]) == ("opposee", "vol")
    for route, corps in [("deblocage", None), ("blocage", None), ("opposition", {"motif": "perte"})]:
        reponse = api.post(f"/cartes/{carte}/{route}", headers=SALMA, json=corps)
        assert reponse.status_code == 409
        assert reponse.json()["detail"]["code"] == "carte_en_opposition"
    assert statut(conn, carte) == "opposee"


def test_une_carte_bloquee_peut_etre_mise_en_opposition(api, conn):
    carte = carte_de(conn, 1)
    api.post(f"/cartes/{carte}/blocage", headers=SALMA)

    assert api.post(f"/cartes/{carte}/opposition", headers=SALMA, json={"motif": "perte"}).status_code == 200


def test_une_verification_a_blanc_ne_change_rien(api, conn):
    carte = carte_de(conn, 1)
    audits = conn.execute("SELECT count(*) AS n FROM audit").fetchone()["n"]

    reponse = api.post(f"/cartes/{carte}/blocage?simulation=true", headers=SALMA)

    assert reponse.json()["statut"] == "bloquee"  # ce que donnerait le blocage…
    assert statut(conn, carte) == "active"  # … sans qu'il ait eu lieu
    assert conn.execute("SELECT count(*) AS n FROM audit").fetchone()["n"] == audits


def test_un_motif_d_opposition_inconnu_est_refuse(api, conn):
    reponse = api.post(f"/cartes/{carte_de(conn, 1)}/opposition", headers=SALMA, json={"motif": "ennui"})

    assert reponse.status_code == 422


# --- Remplacement après une opposition -------------------------------------------------------------------------------


def opposer(api, carte: int, motif: str = "vol") -> None:
    api.post(f"/cartes/{carte}/opposition", headers=SALMA, json={"motif": motif})


def test_apres_une_opposition_une_nouvelle_carte_avec_un_autre_numero(api, conn):
    ancienne = carte_de(conn, 1)
    numero = api.get("/clients/1/cartes", headers=SALMA).json()[0]["numero_masque"]
    opposer(api, ancienne)

    nouvelle = api.post(f"/cartes/{ancienne}/remplacement", headers=SALMA).json()

    assert nouvelle["statut"] == "active" and nouvelle["numero_masque"] != numero
    cartes = {c["id"]: c for c in api.get("/clients/1/cartes", headers=SALMA).json()}
    assert cartes[ancienne]["statut"] == "opposee" and cartes[ancienne]["remplacee_par"] == nouvelle["id"]
    assert derniere_action(conn) == "carte_remplacee"


def test_une_carte_se_remplace_une_seule_fois(api, conn):
    ancienne = carte_de(conn, 1)
    opposer(api, ancienne)
    api.post(f"/cartes/{ancienne}/remplacement", headers=SALMA)

    reponse = api.post(f"/cartes/{ancienne}/remplacement", headers=SALMA)

    assert (reponse.status_code, reponse.json()["detail"]["code"]) == (409, "carte_deja_remplacee")


def test_une_carte_active_ne_se_remplace_pas(api, conn):
    reponse = api.post(f"/cartes/{carte_de(conn, 1)}/remplacement", headers=SALMA)

    assert (reponse.status_code, reponse.json()["detail"]["code"]) == (409, "carte_non_opposee")


def test_la_carte_d_un_autre_client_ne_se_remplace_pas(api, conn):
    assert api.post(f"/cartes/{carte_de(conn, 1)}/remplacement", headers=YOUSSEF).status_code == 404
