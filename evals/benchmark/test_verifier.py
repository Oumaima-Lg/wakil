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


@pytest.mark.parametrize(
    ("question", "obtenu", "reussi"),
    [("3tini relevé dyal chhar 10", 10, True), ("relevé d'octobre", "10", True), ("كشف الحساب ديال أكتوبر", 10, True),
     ("3tini relevé dyal chhar 10", 9, False)],
)  # fmt: skip
def test_le_mois_d_un_releve(question, obtenu, reussi):
    choix = sortie("lister_transactions", {"mois": obtenu})
    assert juger(choix, "lister_transactions", {"mois": 10}, question=question)[0] is reussi


def test_un_mois_que_le_client_n_a_pas_donne_est_invente():
    choix = sortie("lister_transactions", {"mois": 10})
    assert juger(choix, "lister_transactions", question="affichili les opérations dyali") == (
        False,
        "mois inventé : 10",
    )


@pytest.mark.parametrize(("obtenu", "reussi"), [("1200", True), ("•••• 1200", True), ("7919", False)])
def test_la_carte_designee_par_ses_4_chiffres(obtenu, reussi):
    choix = sortie("bloquer_carte", {"carte": obtenu})
    assert juger(choix, "bloquer_carte", {"carte": "1200"}, question="bloqui la carte 1200")[0] is reussi


def test_une_carte_que_le_client_n_a_pas_designee_est_inventee():
    choix = sortie("bloquer_carte", {"carte": "1200"})
    assert juger(choix, "bloquer_carte", question="bloqui liya la carte") == (False, "carte inventé : '1200'")


@pytest.mark.parametrize("question", ["كشف الحساب ديال أكتوبر", "relevé d'octobre", "relevé dyal chhar 10"])
def test_un_mois_nomme_dans_la_phrase_n_est_pas_invente(question):
    """Le client n'a pas demandé de mois précis dans les arguments attendus, mais il l'a bien écrit : pas d'invention."""
    choix = sortie("lister_transactions", {"mois": 10})
    raison = juger(choix, "lister_transactions", question=question)[1]
    assert "inventé" not in raison
