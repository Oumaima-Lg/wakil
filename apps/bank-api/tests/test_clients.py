"""Tests des routes d'un client : profil et comptes."""

SALMA = {"X-Client-Id": "1"}
YOUSSEF = {"X-Client-Id": "2"}


def test_voir_son_profil(api):
    reponse = api.get("/clients/1", headers=SALMA)

    assert reponse.status_code == 200
    assert reponse.json() == {"id": 1, "civilite": "madame", "prenom": "Salma", "nom": "Alaoui", "ville": "Casablanca"}


def test_profil_d_un_autre_client_introuvable(api):
    assert api.get("/clients/1", headers=YOUSSEF).status_code == 404


def test_lister_ses_comptes_avec_rib_masque(api, conn):
    rib = conn.execute("SELECT rib FROM comptes WHERE id = 1").fetchone()["rib"]

    reponse = api.get("/clients/1/comptes", headers=SALMA)

    assert reponse.status_code == 200
    assert reponse.json() == [{"id": 1, "rib_masque": f"•••• {rib[-4:]}", "plafond_virement": "10000.00"}]


def test_comptes_d_un_autre_client_introuvables(api):
    assert api.get("/clients/1/comptes", headers=YOUSSEF).status_code == 404
