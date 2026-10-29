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
