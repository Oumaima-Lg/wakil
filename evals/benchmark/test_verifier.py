"""Tests du juge du benchmark : une erreur ici fausse toute la mesure.

Lancer depuis evals/benchmark : ../../apps/agent-api/.venv/bin/python -m pytest -q test_verifier.py
"""

import pytest
from questions import AUCUN, en_texte
from verifier import get_assert


def juger(sortie: dict, outil, arguments=None, categorie="test", question="q") -> tuple[bool, str]:
    variables = {"outil": outil, "arguments": arguments or {}, "categorie": categorie, "question": question}
    resultat = get_assert(sortie, {"vars": variables})
    return resultat["pass"], resultat["reason"]


def sortie(outil=None, arguments=None, outils=None) -> dict:
    return {
        "outil": outil,
        "arguments": arguments or {},
        "outils": outils if outils is not None else [outil] * bool(outil),
    }


@pytest.mark.parametrize(("choisi", "reussi"), [(None, True), ("analyser_depenses", False)])
def test_aucun_outil_attendu(choisi, reussi):
    assert juger(sortie(choisi), AUCUN)[0] is reussi


@pytest.mark.parametrize(
    ("lus", "reussi"),
    [(["consulter_solde", "lister_factures"], True), (["lister_factures", "consulter_solde"], True),
     (["consulter_solde"], False), (["consulter_solde", "lister_factures", "consulter_plafond"], False)],
)  # fmt: skip
def test_plusieurs_outils_compares_comme_un_ensemble(lus, reussi):
    attendus = en_texte(["consulter_solde", "lister_factures"])
    assert juger(sortie(lus[0], outils=lus), attendus)[0] is reussi


@pytest.mark.parametrize(("obtenu", "reussi"), [("300 DH", True), (300.0, True), ("30", False)])
def test_montant_compare_comme_un_nombre(obtenu, reussi):
    choix = sortie("faire_virement", {"beneficiaire": "l Fatima", "montant": obtenu})
    attendus = {"beneficiaire": "Fatima", "montant": 300}
    assert juger(choix, "faire_virement", attendus, question="sift 300 l Fatima")[0] is reussi


def test_rien_ne_s_invente_dans_une_demande_floue():
    choix = sortie("faire_virement", {"montant": 300})
    assert juger(choix, "faire_virement", categorie="floue") == (False, "montant inventé : 300")


def test_une_categorie_de_depenses_non_nommee_est_inventee():
    choix = sortie("analyser_depenses", {"periode": "ce_mois", "categorie": "taxi"})
    assert juger(choix, "analyser_depenses", {"periode": "ce_mois"}) == (False, "categorie inventé : 'taxi'")


def test_le_mois_oublie_vaut_ce_mois():
    assert juger(sortie("analyser_depenses"), "analyser_depenses", {"periode": "ce_mois"})[0] is True
