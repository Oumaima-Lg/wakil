"""Tests des phrases de Wakil."""

import pytest

from app import reponses


@pytest.mark.parametrize(
    ("montant", "attendu"),
    [("2350.00", "2 350 DH"), ("18500", "18 500 DH"), ("-57.98", "-57,98 DH"), ("0.5", "0,50 DH")],
)
def test_montant_a_la_marocaine(montant, attendu):
    assert reponses.dh(montant) == attendu


def test_factures_impayees():
    factures = [
        {"fournisseur": "Eau & Électricité (démo)", "montant": "312.00"},
        {"fournisseur": "Internet (démo)", "montant": "249.00"},
    ]
    assert reponses.factures(factures).startswith("3ndek 2 factures mazal ma tkhelsou (561 DH f lmjmou3)")


def test_une_seule_facture_impayee_au_singulier():
    factures = [{"fournisseur": "Internet (démo)", "montant": "349.00"}]
    assert reponses.factures(factures) == "3ndek facture wa7da mazal ma tkhelsat :\n- Internet (démo) : 349 DH"


def test_aucune_facture_impayee():
    assert reponses.factures([]) == "Ma 3ndek hta facture mazal ma tkhelsat."


def test_date_affichee_a_l_heure_du_maroc():
    # En juillet 2026, le Maroc était à UTC+1 (base tzdata) : 23 h 30 UTC le 9, c'est déjà le 10 à 0 h 30.
    # Ne jamais écrire « +1 heure » en dur : selon tzdata 2026c, le Maroc est repassé à UTC+0 le 20/09/2026.
    transaction = {"date": "2026-07-09T23:30:00Z", "libelle": "Café", "montant": "-20.00"}
    assert "- 10/07 · Café : -20 DH" in reponses.transactions([transaction])


# --- Morceau 15 : plafond, « toutes les factures », facture désignée par son montant ----------------------------------


def test_plafond_du_compte():
    assert reponses.plafond({"plafond_virement": "10000.00"}) == "Plafond dyalek howa 10 000 DH l kol virement."


def test_une_facture_a_la_fois_liste_les_factures_et_demande_laquelle():
    detail = {"code": "une_a_la_fois", "factures": [{"fournisseur": "Eau & Électricité (démo)", "montant": "312.00"},
                                                    {"fournisseur": "Internet (démo)", "montant": "249.00"}]}  # fmt: skip

    assert reponses.refus("paiement", detail) == (
        "N9der nkhelless ghir facture wa7da f kol merra. 3ndek :\n"
        "- Eau & Électricité (démo) : 312 DH\n- Internet (démo) : 249 DH\nChmen wa7da nbda ?"
    )


@pytest.mark.parametrize(
    ("detail", "attendu"),
    [
        ({"montant": "999.00"}, "Ma 3ndek hta facture dyal 999 DH mazal ma tkhelsat."),
        ({"fournisseur": "Mobile (démo)"}, "Ma 3ndek hta facture dyal Mobile (démo) mazal ma tkhelsat."),
        ({}, "Ma 3ndek hta facture mazal ma tkhelsat."),
    ],
)
def test_aucune_facture_selon_ce_que_le_client_a_designe(detail, attendu):
    assert reponses.refus("paiement", {"code": "facture_absente", **detail}) == attendu


# --- Bénéficiaires et dépenses : les nombres et les totaux viennent du serveur MCP et de la banque --------------------


def test_beneficiaires_avec_leur_nombre():
    resultat = {
        "beneficiaires": [
            {"nom": "Fatima Lahlou", "rib_masque": "•••• 8633"},
            {"nom": "Omar Benali", "rib_masque": "•••• 1120"},
        ],
        "nombre": 2,
    }
    assert reponses.beneficiaires(resultat) == (
        "3ndek 2 bénéficiaires :\n- Fatima Lahlou (•••• 8633)\n- Omar Benali (•••• 1120)"
    )


def test_aucun_beneficiaire():
    assert reponses.beneficiaires({"beneficiaires": [], "nombre": 0}) == "Ma 3ndek hta bénéficiaire."


DEPENSES_OCTOBRE = {
    "periode": "ce_mois",
    "du": "2026-10-01",
    "au": "2026-10-30",
    "depenses": "1012.50",
    "entrees": "6000.00",
    "nombre": 5,
    "par_categorie": [
        {"categorie": "virements", "nom": "Virements envoyés", "total": "500.00", "nombre": 1},
        {"categorie": "factures", "nom": "Factures", "total": "312.00", "nombre": 1},
        {"categorie": "restaurant", "nom": "Restaurant", "total": "200.50", "nombre": 2},
    ],
    "plus_grosse": {"id": 9, "date": "2026-10-20T10:00:00Z", "montant": "-500.00", "libelle": "Virement vers Fatima"},
    "categorie": None,
}


def test_depenses_du_mois():
    assert reponses.depenses(DEPENSES_OCTOBRE) == (
        "Had chhar (octobre) : srefti 1 012,50 DH w dkhel lik 6 000 DH (5 d l'opérations).\n"
        "Fin srefti ktar :\n- Virements envoyés : 500 DH\n- Factures : 312 DH\n- Restaurant : 200,50 DH\n"
        "Akbar masrouf : Virement vers Fatima, 500 DH (20/10)."
    )


def test_depenses_d_une_categorie_le_mois_dernier():
    resultat = DEPENSES_OCTOBRE | {
        "periode": "mois_dernier",
        "du": "2026-09-01",
        "categorie": {"categorie": "restaurant", "nom": "Restaurant", "total": "200.50", "nombre": 2},
    }
    assert reponses.depenses(resultat) == (
        "Chhar li fat (septembre), srefti 200,50 DH f Restaurant (2 d l'opérations)."
    )


def test_depenses_d_une_categorie_vide():
    resultat = DEPENSES_OCTOBRE | {"categorie": {"categorie": "taxi", "nom": "Taxi", "total": "0.00", "nombre": 0}}
    assert reponses.depenses(resultat) == "Ma srefti walou f Taxi had chhar (octobre)."
