"""Tests de la case du graphe qui cite la FAQ, sans Ollama ni serveur MCP : l'outil question_faq est simulé.

Les fiches et la recherche elles-mêmes sont testées dans apps/rag-faq.
"""

from app import agent, outils, reponses

FICHE_FRAIS = {"fiche": "frais", "titre": "Frais et tarifs", "texte": "La Banque Atlas Démo ne prélève aucun frais.",
               "similarite": 0.82}  # fmt: skip


def faux_serveur_faq(monkeypatch, fiche=None, panne=False):
    """Remplace l'appel au serveur MCP de la FAQ ; garde chaque appel (client, outil, arguments)."""
    appels = []

    def appeler(client_id, nom, arguments, confirme=False):
        appels.append((client_id, nom, arguments))
        if panne:
            raise outils.OutilsIndisponibles("le serveur MCP de la FAQ ne répond pas")
        return {"fiche": fiche}

    monkeypatch.setattr(outils, "appeler", appeler)
    return appels


def test_la_fiche_est_citee_telle_quelle_avec_son_titre(faux_llm, tour, monkeypatch):
    faux_llm(agent.OUTIL_FAQ)
    appels = faux_serveur_faq(monkeypatch, FICHE_FRAIS)

    etat = tour("wach l virement fih frais ?")

    assert etat["reponse"] == reponses.faq("Frais et tarifs", "La Banque Atlas Démo ne prélève aucun frais.")
    assert etat["resultat"]["titre"] == "Frais et tarifs"
    # La phrase du client, pas une reformulation du LLM ; et sans dire au serveur de la FAQ qui est le client.
    assert appels == [(None, "question_faq", {"question": "wach l virement fih frais ?"})]


def test_aucune_fiche_assez_proche_wakil_le_dit(faux_llm, tour, monkeypatch):
    faux_llm(agent.OUTIL_FAQ)
    faux_serveur_faq(monkeypatch, fiche=None)

    etat = tour("chkoun rbe7 lmatch lbare7 ?")

    assert etat["reponse"] == reponses.FAQ_INTROUVABLE
    assert etat["resultat"] is None


def test_faq_en_panne(faux_llm, tour, monkeypatch):
    faux_llm(agent.OUTIL_FAQ)
    faux_serveur_faq(monkeypatch, panne=True)

    etat = tour("wach l virement fih frais ?")

    assert (etat["reponse"], etat["erreur"]) == (reponses.FAQ_INDISPONIBLE, True)


def test_le_prompt_systeme_dit_quand_appeler_la_faq():
    """Sans cette phrase, le prompt ordonnait de refuser tout ce qui ne concerne pas le compte (bug du 27/10/2026)."""
    assert agent.OUTIL_FAQ in agent.SYSTEME
