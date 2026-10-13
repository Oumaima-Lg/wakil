"""Tests des routes des factures."""

SALMA = {"X-Client-Id": "1"}
YOUSSEF = {"X-Client-Id": "2"}
EAU = "Eau & Électricité (démo)"


def factures(api, entetes, client_id):
    return api.get(f"/clients/{client_id}/factures", headers=entetes).json()


def facture_impayee(api, entetes, client_id, fournisseur):
    return next(
        f for f in factures(api, entetes, client_id) if f["fournisseur"] == fournisseur and f["statut"] == "impayee"
    )


def test_lister_ses_factures(api):
    reponse = api.get("/clients/1/factures", headers=SALMA)
    assert reponse.status_code == 200
    impayees = [(f["fournisseur"], f["montant"]) for f in reponse.json() if f["statut"] == "impayee"]
    assert impayees == [(EAU, "312.00"), ("Internet (démo)", "249.00")]


def test_factures_d_un_autre_client_introuvables(api):
    assert api.get("/clients/1/factures", headers=YOUSSEF).status_code == 404


def test_payer_une_facture(api, conn):
    eau = facture_impayee(api, SALMA, 1, EAU)

    reponse = api.post(f"/factures/{eau['id']}/payer", headers=SALMA)

    assert reponse.status_code == 200
    assert reponse.json()["nouveau_solde"] == "2038.00"  # 2 350 - 312
    statuts = {f["id"]: f["statut"] for f in factures(api, SALMA, 1)}
    assert statuts[eau["id"]] == "payee"
    derniere = api.get("/comptes/1/transactions?limite=1", headers=SALMA).json()[0]
    assert (derniere["montant"], derniere["libelle"]) == ("-312.00", f"Paiement facture {EAU}")
    audit = conn.execute("SELECT action, details FROM audit WHERE client_id = 1 ORDER BY id DESC LIMIT 1").fetchone()
    assert audit["action"] == "paiement_facture"
    assert audit["details"]["facture_id"] == eau["id"]


def test_payer_deux_fois_la_meme_facture_refuse(api):
    eau = facture_impayee(api, SALMA, 1, EAU)
    assert api.post(f"/factures/{eau['id']}/payer", headers=SALMA).status_code == 200

    reponse = api.post(f"/factures/{eau['id']}/payer", headers=SALMA)

    assert reponse.status_code == 409
    assert reponse.json()["detail"] == "Facture déjà payée"


def test_payer_sans_solde_suffisant_refuse(api):
    internet = facture_impayee(api, YOUSSEF, 2, "Internet (démo)")  # 349 DH pour un solde de 150 DH

    reponse = api.post(f"/factures/{internet['id']}/payer", headers=YOUSSEF)

    assert reponse.status_code == 409
    assert reponse.json()["detail"] == "Solde insuffisant"
    assert api.get("/comptes/2/solde", headers=YOUSSEF).json()["solde"] == "150.00"


def test_payer_la_facture_d_un_autre_client_refuse(api):
    eau = facture_impayee(api, SALMA, 1, EAU)
    assert api.post(f"/factures/{eau['id']}/payer", headers=YOUSSEF).status_code == 404
