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
