"""Tests des routes des comptes."""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

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


def ajouter_operations(conn, compte_id: int, operations: list[tuple[str, str, str]]) -> None:
    """Des opérations en janvier 2020, loin des fausses données (60 derniers jours) : les totaux sont connus."""
    for quand, montant, libelle in operations:
        conn.execute(
            "INSERT INTO transactions (compte_id, date, montant, libelle) VALUES (%s, %s::timestamptz, %s, %s)",
            (compte_id, f"{quand} Africa/Casablanca", montant, libelle),
        )


def test_depenses_calculees_par_la_banque(api, conn):
    ajouter_operations(
        conn,
        1,
        [
            ("2020-01-05 12:00", "-120.50", "Restaurant"),
            ("2020-01-12 20:00", "-80.00", "Restaurant"),
            ("2020-01-15 09:00", "-312.00", "Paiement facture Eau & Électricité (démo)"),
            ("2020-01-20 10:00", "-500.00", "Virement vers Fatima Lahlou"),
            ("2020-01-25 08:00", "6000.00", "Salaire (démo)"),
        ],
    )
    reponse = api.get("/comptes/1/depenses?du=2020-01-01&au=2020-01-31", headers=SALMA)
    assert reponse.status_code == 200
    resume = reponse.json()
    assert (resume["depenses"], resume["entrees"], resume["nombre"]) == ("1012.50", "6000.00", 5)
    assert [(c["categorie"], c["total"], c["nombre"]) for c in resume["par_categorie"]] == [
        ("virements", "500.00", 1),
        ("factures", "312.00", 1),
        ("restaurant", "200.50", 2),
    ]
    assert resume["plus_grosse"]["libelle"] == "Virement vers Fatima Lahlou"


def test_depenses_comptees_au_jour_du_maroc(api, conn):
    """00 h 30 le 1er février au Maroc, c'est encore le 31 janvier en temps universel : l'opération est de février."""
    ajouter_operations(conn, 1, [("2020-01-31 23:30", "-10.00", "Café"), ("2020-02-01 00:30", "-99.00", "Taxi")])
    resume = api.get("/comptes/1/depenses?du=2020-01-01&au=2020-01-31", headers=SALMA).json()
    assert (resume["depenses"], resume["nombre"]) == ("10.00", 1)


def test_depenses_d_une_periode_sans_operation(api):
    resume = api.get("/comptes/1/depenses?du=2019-01-01&au=2019-01-31", headers=SALMA).json()
    assert (resume["depenses"], resume["entrees"], resume["nombre"]) == ("0.00", "0.00", 0)
    assert resume["par_categorie"] == [] and resume["plus_grosse"] is None


def test_depenses_dates_inversees_refusees(api):
    reponse = api.get("/comptes/1/depenses?du=2020-02-01&au=2020-01-01", headers=SALMA)
    assert reponse.status_code == 422


def test_depenses_du_compte_d_un_autre_client_introuvables(api):
    reponse = api.get("/comptes/1/depenses?du=2020-01-01&au=2020-01-31", headers=YOUSSEF)
    assert reponse.status_code == 404


# --- Opérations filtrées, page par page, détail et relevé -----------------------------------------------------------

JANVIER_2020 = [
    ("2020-01-03 10:00", "-40.00", "Café"),
    ("2020-01-08 12:00", "-120.00", "Restaurant"),
    ("2020-01-15 09:00", "5000.00", "Salaire (démo)"),
    ("2020-01-20 18:00", "-300.00", "Courses supermarché"),
    ("2020-01-28 08:00", "-60.00", "Taxi"),
]


def lien_suivant(reponse) -> str | None:
    """L'adresse de la page suivante, lue dans l'en-tête Link (<…>; rel="next")."""
    lien = reponse.headers.get("link")
    return lien.split(";")[0].strip("<> ") if lien else None


def test_operations_entre_deux_dates(api, conn):
    ajouter_operations(conn, 1, JANVIER_2020)

    reponse = api.get("/comptes/1/transactions?du=2020-01-05&au=2020-01-25&limite=50", headers=SALMA)

    assert [t["libelle"] for t in reponse.json()] == ["Courses supermarché", "Salaire (démo)", "Restaurant"]


def test_operations_page_par_page_sans_rien_sauter_ni_repeter(api, conn):
    ajouter_operations(conn, 1, JANVIER_2020)
    adresse, lues, pages = "/comptes/1/transactions?du=2020-01-01&au=2020-01-31&limite=2", [], 0

    while adresse:
        reponse = api.get(adresse, headers=SALMA)
        lues += [t["libelle"] for t in reponse.json()]
        adresse, pages = lien_suivant(reponse), pages + 1

    assert pages == 3  # 2 + 2 + 1 ; la dernière page n'a pas d'en-tête Link
    assert lues == ["Taxi", "Courses supermarché", "Salaire (démo)", "Restaurant", "Café"]


def test_un_curseur_invalide_est_refuse(api):
    assert api.get("/comptes/1/transactions?curseur=nimporte-quoi", headers=SALMA).status_code == 422


def test_detail_d_une_operation(api, conn):
    operation = api.get("/comptes/1/transactions?limite=1", headers=SALMA).json()[0]

    assert api.get(f"/comptes/1/transactions/{operation['id']}", headers=SALMA).json() == operation


def test_detail_d_une_operation_d_un_autre_compte_introuvable(api, conn):
    autre = conn.execute("SELECT id FROM transactions WHERE compte_id = 2 LIMIT 1").fetchone()["id"]

    assert api.get(f"/comptes/1/transactions/{autre}", headers=SALMA).status_code == 404
    assert api.get(f"/comptes/1/transactions/{autre}", headers=YOUSSEF).status_code == 404


def test_releve_mensuel_qui_tombe_juste(api, conn):
    ajouter_operations(conn, 1, JANVIER_2020)

    releve = api.get("/comptes/1/releves/2020-01", headers=SALMA).json()

    assert [t["libelle"] for t in releve["transactions"]] == [libelle for _, _, libelle in JANVIER_2020]  # dans l'ordre
    assert (releve["du"], releve["au"], releve["complet"]) == ("2020-01-01", "2020-01-31", True)
    assert (releve["total_entrees"], releve["total_sorties"]) == ("5000.00", "520.00")
    ouverture, cloture = Decimal(releve["solde_ouverture"]), Decimal(releve["solde_cloture"])
    assert ouverture + Decimal("5000.00") - Decimal("520.00") == cloture
    # Fin janvier 2020 = solde actuel moins tout ce qui s'est passé depuis
    depuis = conn.execute(
        "SELECT coalesce(sum(montant), 0) AS s FROM transactions WHERE compte_id = 1 AND date >= '2020-02-01 Africa/Casablanca'"
    ).fetchone()["s"]
    assert cloture == Decimal("2350.00") - depuis


def test_releve_du_mois_en_cours_pas_encore_complet(api):
    mois = datetime.now(ZoneInfo("Africa/Casablanca")).strftime("%Y-%m")

    assert api.get(f"/comptes/1/releves/{mois}", headers=SALMA).json()["complet"] is False


@pytest.mark.parametrize(("mois", "code"), [("2999-01", 404), ("2020-13", 422), ("janvier", 422)])
def test_releve_d_un_mois_futur_ou_mal_ecrit(api, mois, code):
    assert api.get(f"/comptes/1/releves/{mois}", headers=SALMA).status_code == code


def test_releve_du_compte_d_un_autre_client_introuvable(api):
    assert api.get("/comptes/1/releves/2020-01", headers=YOUSSEF).status_code == 404
