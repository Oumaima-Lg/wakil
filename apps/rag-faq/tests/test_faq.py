"""Tests de la FAQ sans Ollama ni base : les fiches elles-mêmes, le seuil, et l'écriture des vecteurs."""

import re

import pytest

from app import faq

FICHES = faq.lire_fiches()


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
def test_une_fiche_sous_le_seuil_n_est_pas_retenue(monkeypatch, similarite, trouvee):
    monkeypatch.setattr(faq, "classer", lambda question, nombre: [faq.Trouvaille("x", "X", "…", similarite)])

    assert (faq.chercher("n'importe quoi") is not None) is trouvee


def test_sans_base_configuree_la_faq_se_dit_indisponible(monkeypatch):
    monkeypatch.setattr(faq, "_pool", None)
    monkeypatch.delenv("FAQ_POSTGRES_USER", raising=False)

    with pytest.raises(faq.FaqIndisponible):
        faq.chercher("ch7al kayt5lles l virement ?")


def test_un_vecteur_s_ecrit_comme_pgvector_le_lit():
    assert faq._vecteur([0.5, -0.25, 1.0]) == "[0.5,-0.25,1.0]"
