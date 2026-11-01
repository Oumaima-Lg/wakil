"""Tests du mode sécurité : tant que la carte est bloquée ou en opposition, Wakil ne fait rien (choix du 31/10/2026)."""

import pytest

from app import agent, outils, reponses
from app.agent import carte_qui_bloque  # la vraie fonction (conftest la remplace sur agent)

BLOQUEE = {"numero_masque": "•••• 7919", "statut": "bloquee", "motif_opposition": None}
OPPOSEE = {"numero_masque": "•••• 7919", "statut": "opposee", "motif_opposition": "vol"}
ACTIVE = {"numero_masque": "•••• 4200", "statut": "active", "motif_opposition": None}


@pytest.fixture
def carte(monkeypatch):
    """Fixe la carte qui bloque Wakil (ou None) pour ce test."""

    def fixer(etat):
        monkeypatch.setattr(agent, "carte_qui_bloque", lambda client_id: etat)

    return fixer


@pytest.mark.parametrize("demande", ["chhal f compte dyali ?", "sifet 200 l Fatima", "chno homa les frais ?"])
def test_carte_bloquee_wakil_ne_fait_rien_et_dit_quoi_faire(faux_llm, tour, carte, demande):
    faux = faux_llm("consulter_solde")
    carte(BLOQUEE)

    etat = tour(demande)

    assert etat["reponse"] == reponses.mode_securite(BLOQUEE)
    assert "Debloquiha f l'espace dyalek (Ma carte)" in etat["reponse"]
    assert faux.appels == 0  # même pas le LLM


def test_carte_en_opposition_il_faut_commander_une_nouvelle_carte(faux_llm, tour, carte):
    faux_llm("consulter_solde")
    carte(OPPOSEE)

    assert "Commandi carte jdida" in tour("chhal f compte dyali ?")["reponse"]


def test_le_bouton_payer_avec_wakil_est_aussi_arrete(tour, carte):
    carte(BLOQUEE)

    etat = agent.wakil.invoke(agent.nouveau_tour("Payer", 1, facture_id=1), agent.config(1, "bouton-payer"))

    assert etat["reponse"] == reponses.mode_securite(BLOQUEE)
    assert etat.get("operation") is None  # aucune carte de confirmation


def test_un_salut_reste_un_salut(faux_llm, tour, carte):
    carte(BLOQUEE)

    assert tour("salam")["reponse"] == reponses.SALUT


@pytest.mark.parametrize(
    ("cartes", "attendue"),
    [
        ([ACTIVE], None),
        ([BLOQUEE], BLOQUEE),
        ([OPPOSEE], OPPOSEE),  # pas encore de nouvelle carte
        ([OPPOSEE, ACTIVE], None),  # la nouvelle carte est active : Wakil refonctionne
        ([], None),
    ],
)
def test_la_carte_qui_met_wakil_en_mode_securite(monkeypatch, cartes, attendue):
    monkeypatch.setattr(outils, "appeler", lambda client_id, nom, arguments, **options: {"cartes": cartes})

    assert carte_qui_bloque(1) == attendue


def test_si_la_banque_ne_repond_pas_la_demande_suit_son_cours(monkeypatch):
    def panne(client_id, nom, arguments, **options):
        raise outils.OutilsIndisponibles("serveur MCP arrêté")

    monkeypatch.setattr(outils, "appeler", panne)

    assert carte_qui_bloque(1) is None
