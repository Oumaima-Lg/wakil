"""Tests du serveur MCP de la FAQ, en HTTP, avec le client MCP officiel (comme agent-api). Sans Ollama ni base."""

from app import faq

FRAIS = faq.Trouvaille("frais", "Frais et tarifs", "La Banque Atlas Démo ne prélève aucun frais.", 0.82)


def test_le_serveur_annonce_un_seul_outil_en_lecture_seule(mcp):
    outils = mcp.lister()

    assert [o.name for o in outils] == ["question_faq"]
    assert outils[0].annotations.read_only_hint is True
    assert outils[0].input_schema["required"] == ["question"]
    assert "frais" in outils[0].description  # la description que lira le LLM de l'agent


def test_la_fiche_trouvee_est_renvoyee_telle_quelle(mcp, monkeypatch):
    cherche = []
    monkeypatch.setattr(faq, "chercher", lambda question: cherche.append(question) or FRAIS)

    appel = mcp("question_faq", {"question": "wach l virement fih frais ?"})

    assert not appel.is_error
    assert appel.structured_content == {
        "fiche": {"fiche": "frais", "titre": "Frais et tarifs", "texte": FRAIS.texte, "similarite": 0.82}
    }
    assert cherche == ["wach l virement fih frais ?"]


def test_sous_le_seuil_aucune_fiche(mcp, monkeypatch):
    monkeypatch.setattr(faq, "chercher", lambda question: None)

    assert mcp("question_faq", {"question": "chkoun rbe7 lmatch ?"}).structured_content == {"fiche": None}


def test_faq_en_panne_donne_une_erreur_d_outil(mcp, monkeypatch):
    def en_panne(question):
        raise faq.FaqIndisponible("Ollama ne répond pas")

    monkeypatch.setattr(faq, "chercher", en_panne)

    appel = mcp("question_faq", {"question": "wach l virement fih frais ?"})

    assert appel.is_error
    assert "FAQ indisponible" in appel.content[0].text
