"""Tests des routes des factures."""

SALMA = {"X-Client-Id": "1"}
YOUSSEF = {"X-Client-Id": "2"}
EAU = "Eau & Électricité (démo)"


def factures(api, entetes, client_id):
    return api.get(f"/clients/{client_id}/factures", headers=entetes).json()


def nombre_d_audits(conn):
    return conn.execute("SELECT count(*) AS n FROM audit").fetchone()["n"]


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
    assert reponse.json()["simulation"] is False
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
    assert reponse.json()["detail"] == {"code": "facture_deja_payee", "message": "Facture déjà payée"}


def test_payer_sans_solde_suffisant_refuse(api):
    internet = facture_impayee(api, YOUSSEF, 2, "Internet (démo)")  # 349 DH pour un solde de 150 DH

    reponse = api.post(f"/factures/{internet['id']}/payer", headers=YOUSSEF)

    assert reponse.status_code == 409
    # Le code et les montants servent à l'agent pour expliquer le refus, sans rien recalculer
    assert reponse.json()["detail"] == {
        "code": "solde_insuffisant",
        "message": "Solde insuffisant",
        "solde": "150.00",
        "montant": "349.00",
    }
    assert api.get("/comptes/2/solde", headers=YOUSSEF).json()["solde"] == "150.00"


def test_payer_la_facture_d_un_autre_client_refuse(api):
    eau = facture_impayee(api, SALMA, 1, EAU)
    assert api.post(f"/factures/{eau['id']}/payer", headers=YOUSSEF).status_code == 404


def test_simuler_un_paiement_ne_change_rien(api, conn):
    eau = facture_impayee(api, SALMA, 1, EAU)
    derniere_avant = api.get("/comptes/1/transactions?limite=1", headers=SALMA).json()[0]
    audits_avant = nombre_d_audits(conn)

    reponse = api.post(f"/factures/{eau['id']}/payer?simulation=true", headers=SALMA)

    assert reponse.status_code == 200
    assert reponse.json() == {
        "facture_id": eau["id"],
        "fournisseur": EAU,
        "montant": "312.00",
        "nouveau_solde": "2038.00",  # calculé par la vraie requête, puis annulé
        "simulation": True,
    }
    assert api.get("/comptes/1/solde", headers=SALMA).json()["solde"] == "2350.00"
    assert facture_impayee(api, SALMA, 1, EAU)["id"] == eau["id"]  # toujours à payer
    assert api.get("/comptes/1/transactions?limite=1", headers=SALMA).json()[0] == derniere_avant
    assert nombre_d_audits(conn) == audits_avant


def test_simuler_un_paiement_sans_solde_suffisant_donne_le_refus(api):
    internet = facture_impayee(api, YOUSSEF, 2, "Internet (démo)")

    reponse = api.post(f"/factures/{internet['id']}/payer?simulation=true", headers=YOUSSEF)

    assert reponse.status_code == 409
    assert reponse.json()["detail"]["code"] == "solde_insuffisant"


def test_simuler_puis_payer_pour_de_vrai(api):
    eau = facture_impayee(api, SALMA, 1, EAU)
    simulation = api.post(f"/factures/{eau['id']}/payer?simulation=true", headers=SALMA).json()

    paiement = api.post(f"/factures/{eau['id']}/payer", headers=SALMA).json()

    assert paiement["nouveau_solde"] == simulation["nouveau_solde"]  # la carte annonçait le bon solde
