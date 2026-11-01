"""Tests de l'idempotence : rejouer une opération avec la même clé ne la refait jamais."""

SALMA = {"X-Client-Id": "1"}
YOUSSEF = {"X-Client-Id": "2"}
EAU = "Eau & Électricité (démo)"


def avec_cle(entetes: dict, cle: str) -> dict:
    return {**entetes, "Idempotency-Key": cle}


def solde(conn, client_id: int):
    return conn.execute("SELECT solde FROM comptes WHERE client_id = %s", (client_id,)).fetchone()["solde"]


def nombre(conn, table: str) -> int:
    return conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]


def facture_d_eau(conn) -> int:
    return conn.execute(
        "SELECT id FROM factures WHERE client_id = 1 AND fournisseur = %s AND statut = 'impayee'", (EAU,)
    ).fetchone()["id"]


def beneficiaire_de_salma(conn) -> int:
    return conn.execute("SELECT id FROM beneficiaires WHERE client_id = 1 ORDER BY id LIMIT 1").fetchone()["id"]


def test_un_paiement_rejoue_avec_la_meme_cle_n_est_fait_qu_une_fois(api, conn):
    facture = facture_d_eau(conn)
    transactions = nombre(conn, "transactions")

    premiere = api.post(f"/factures/{facture}/payer", headers=avec_cle(SALMA, "carte-1"))
    rejouee = api.post(f"/factures/{facture}/payer", headers=avec_cle(SALMA, "carte-1"))

    assert premiere.status_code == rejouee.status_code == 200
    assert rejouee.json() == premiere.json()  # la même réponse, et pas « facture déjà payée »
    assert solde(conn, 1) == 2350 - 312  # débité une seule fois
    assert nombre(conn, "transactions") == transactions + 1


def test_un_virement_rejoue_avec_la_meme_cle_n_est_fait_qu_une_fois(api, conn):
    demande = {"beneficiaire_id": beneficiaire_de_salma(conn), "montant": "500"}
    audits = nombre(conn, "audit")

    for _ in range(3):
        reponse = api.post("/virements", headers=avec_cle(SALMA, "carte-2"), json=demande)
        assert reponse.status_code == 200 and reponse.json()["nouveau_solde"] == "1850.00"

    assert solde(conn, 1) == 1850
    assert nombre(conn, "audit") == audits + 1


def test_une_cle_reutilisee_pour_une_autre_demande_est_refusee(api, conn):
    beneficiaire = beneficiaire_de_salma(conn)
    api.post("/virements", headers=avec_cle(SALMA, "carte-3"), json={"beneficiaire_id": beneficiaire, "montant": "500"})

    autre = api.post(
        "/virements", headers=avec_cle(SALMA, "carte-3"), json={"beneficiaire_id": beneficiaire, "montant": "900"}
    )

    assert autre.status_code == 409
    assert autre.json()["detail"]["code"] == "cle_reutilisee"
    assert solde(conn, 1) == 1850  # le second montant n'est jamais parti


def test_sans_cle_chaque_demande_est_une_nouvelle_operation(api, conn):
    demande = {"beneficiaire_id": beneficiaire_de_salma(conn), "montant": "100"}

    api.post("/virements", headers=SALMA, json=demande)
    api.post("/virements", headers=SALMA, json=demande)

    assert solde(conn, 1) == 2150


def test_une_verification_a_blanc_ne_garde_pas_de_cle(api, conn):
    reponse = api.post(f"/factures/{facture_d_eau(conn)}/payer?simulation=true", headers=avec_cle(SALMA, "carte-4"))

    assert reponse.status_code == 200
    assert nombre(conn, "idempotence") == 0


def test_un_refus_ne_garde_pas_la_cle(api, conn):
    """Youssef n'a pas assez d'argent : rien n'a bougé, la même demande pourra être refaite plus tard."""
    facture = conn.execute("SELECT id FROM factures WHERE client_id = 2 AND statut = 'impayee' LIMIT 1").fetchone()

    reponse = api.post(f"/factures/{facture['id']}/payer", headers=avec_cle(YOUSSEF, "carte-5"))

    assert reponse.json()["detail"]["code"] == "solde_insuffisant"
    assert nombre(conn, "idempotence") == 0


def test_chaque_client_a_ses_propres_cles(api, conn):
    api.post(f"/factures/{facture_d_eau(conn)}/payer", headers=avec_cle(SALMA, "carte-6"))
    facture_de_youssef = conn.execute("SELECT id FROM factures WHERE client_id = 2 LIMIT 1").fetchone()["id"]

    reponse = api.post(f"/factures/{facture_de_youssef}/payer", headers=avec_cle(YOUSSEF, "carte-6"))

    assert reponse.json()["detail"]["code"] != "cle_reutilisee"  # la clé de Salma n'existe pas pour Youssef


def test_une_cle_de_plus_de_24_heures_est_oubliee(api, conn):
    demande = {"beneficiaire_id": beneficiaire_de_salma(conn), "montant": "100"}
    api.post("/virements", headers=avec_cle(SALMA, "carte-7"), json=demande)
    conn.execute("UPDATE idempotence SET cree_le = now() - interval '25 hours'")

    api.post("/virements", headers=avec_cle(SALMA, "carte-7"), json=demande)

    assert solde(conn, 1) == 2150  # la seconde demande est une nouvelle opération


def test_une_cle_mal_formee_est_refusee(api, conn):
    reponse = api.post(f"/factures/{facture_d_eau(conn)}/payer", headers=avec_cle(SALMA, "pas de espaces !"))

    assert reponse.status_code == 422
