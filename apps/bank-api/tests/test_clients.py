"""Tests des routes d'un client : profil et comptes."""

from conftest import entetes

SALMA = entetes(1)
YOUSSEF = entetes(2)


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


def test_lister_ses_beneficiaires(api):
    reponse = api.get("/clients/1/beneficiaires", headers=SALMA)

    assert reponse.status_code == 200
    beneficiaires = [{k: v for k, v in b.items() if k != "id"} for b in reponse.json()]
    assert beneficiaires == [{"nom": "Fatima Lahlou", "rib_masque": "•••• 8633", "interne": True}]


def test_beneficiaires_d_un_autre_client_introuvables(api):
    assert api.get("/clients/1/beneficiaires", headers=YOUSSEF).status_code == 404


# --- Journal d'audit visible par le client -------------------------------------------------------------------------


def test_le_journal_montre_ce_qui_a_ete_fait_en_phrases_lisibles(api, conn, carte_neuve):
    facture = conn.execute(
        "SELECT id FROM factures WHERE client_id = 1 AND fournisseur = 'Internet (démo)' AND statut = 'impayee'"
    ).fetchone()["id"]
    carte = carte_neuve
    api.post(f"/factures/{facture}/payer", headers=SALMA)
    numero = api.post(f"/cartes/{carte}/blocage", headers=SALMA).json()["numero_masque"]

    journal = api.get("/clients/1/audit", headers=SALMA).json()

    assert [(e["action"], e["libelle"], e["montant"]) for e in journal[:2]] == [
        ("carte_bloquee", f"Carte {numero} bloquée", None),  # la plus récente d'abord
        ("paiement_facture", "Paiement de la facture Internet (démo)", "249.00"),
    ]
    assert set(journal[0]) == {"date", "action", "libelle", "montant"}  # aucun identifiant interne


def test_le_journal_d_un_autre_client_est_introuvable(api):
    assert api.get("/clients/1/audit", headers=YOUSSEF).status_code == 404
