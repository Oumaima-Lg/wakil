"""Tests de la FAQ sans Ollama ni base : les fiches elles-mêmes, le seuil, et la case du graphe qui les cite."""

import re

import pytest

from app import agent, faq, reponses

FICHES = faq.lire_fiches()
FICHE_FRAIS = faq.Trouvaille("frais", "Frais et tarifs", "La Banque Atlas Démo ne prélève aucun frais.", 0.82)


# --- Les fiches (data/faq/faq.yaml) ---------------------------------------------------------------------------------


def test_chaque_fiche_a_un_id_unique_un_titre_un_texte_et_des_questions():
    ids = [f["id"] for f in FICHES]
    assert len(ids) == len(set(ids))
    for fiche in FICHES:
        assert fiche["titre"].strip() and fiche["texte"].strip()
        assert len(fiche["questions"]) >= 4, fiche["id"]


def test_chaque_fiche_a_des_questions_en_lettres_arabes_et_latines():
    """Les questions types servent de pont entre la darija du client et le texte français de la fiche."""
    arabe = re.compile(r"[؀-ۿ]")
    for fiche in FICHES:
        assert any(arabe.search(q) for q in fiche["questions"]), fiche["id"]
        assert any(not arabe.search(q) for q in fiche["questions"]), fiche["id"]


def test_une_question_type_n_appartient_qu_a_une_fiche():
    questions = [q for f in FICHES for q in f["questions"]]
    assert len(questions) == len(set(questions))


def test_les_fiches_ne_citent_que_les_fournisseurs_de_demo():
    textes = " ".join(f["texte"] for f in FICHES)
    for fournisseur in re.findall(r"[A-ZÉ][\w &]+ \(démo\)", textes):
        assert fournisseur in {"Eau & Électricité (démo)", "Internet (démo)", "Mobile (démo)"}


# --- Le seuil -------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("similarite", "trouvee"), [(faq.SEUIL, True), (0.95, True), (faq.SEUIL - 0.01, False)])
def test_une_fiche_sous_le_seuil_n_est_pas_citee(monkeypatch, similarite, trouvee):
    monkeypatch.setattr(faq, "classer", lambda question, nombre: [faq.Trouvaille("x", "X", "…", similarite)])

    assert (faq.chercher("n'importe quoi") is not None) is trouvee


def test_sans_base_la_faq_se_dit_indisponible(monkeypatch):
    monkeypatch.setattr(faq, "pool", None)

    with pytest.raises(faq.FaqIndisponible):
        faq.chercher("ch7al kayt5lles l virement ?")


def test_un_vecteur_s_ecrit_comme_pgvector_le_lit():
    assert faq._vecteur([0.5, -0.25, 1.0]) == "[0.5,-0.25,1.0]"


# --- La case du graphe ----------------------------------------------------------------------------------------------


def test_la_fiche_est_citee_telle_quelle_avec_son_titre(faux_llm, tour, monkeypatch):
    cherche = []
    faux_llm(agent.OUTIL_FAQ)
    monkeypatch.setattr(faq, "chercher", lambda question: cherche.append(question) or FICHE_FRAIS)

    etat = tour("wach l virement fih frais ?")

    assert etat["reponse"] == reponses.faq("Frais et tarifs", "La Banque Atlas Démo ne prélève aucun frais.")
    assert etat["resultat"]["titre"] == "Frais et tarifs"
    assert cherche == ["wach l virement fih frais ?"]  # la phrase du client, pas une reformulation du LLM


def test_aucune_fiche_assez_proche_wakil_le_dit(faux_llm, tour, monkeypatch):
    faux_llm(agent.OUTIL_FAQ)
    monkeypatch.setattr(faq, "chercher", lambda question: None)

    etat = tour("chkoun rbe7 lmatch lbare7 ?")

    assert etat["reponse"] == reponses.FAQ_INTROUVABLE
    assert etat["resultat"] is None


def test_faq_en_panne(faux_llm, tour, monkeypatch):
    faux_llm(agent.OUTIL_FAQ)

    def en_panne(question):
        raise faq.FaqIndisponible("Ollama ne répond pas")

    monkeypatch.setattr(faq, "chercher", en_panne)

    etat = tour("wach l virement fih frais ?")

    assert (etat["reponse"], etat["erreur"]) == (reponses.FAQ_INDISPONIBLE, True)


def test_la_faq_est_proposee_au_llm_sans_parametre():
    assert agent.DESCRIPTION_FAQ["function"]["name"] == agent.OUTIL_FAQ
    assert agent.DESCRIPTION_FAQ["function"]["parameters"]["properties"] == {}


def test_le_prompt_systeme_dit_quand_appeler_la_faq():
    """Sans cette phrase, le prompt ordonnait de refuser tout ce qui ne concerne pas le compte (bug du 27/10/2026)."""
    assert agent.OUTIL_FAQ in agent.SYSTEME
