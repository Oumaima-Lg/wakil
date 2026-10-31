"""Tests du mode json du fournisseur (modèles sans appel d'outils natif), sans Ollama ni serveur MCP.

Lancer depuis evals/benchmark : ../../apps/agent-api/.venv/bin/python -m pytest -q test_fournisseur.py
"""

from fournisseur import appels_du_json, historique_json, outils_en_texte
from langchain_core.messages import AIMessage, HumanMessage

DESCRIPTIONS = [
    {"type": "function", "function": {"name": "consulter_solde", "description": "Donne le solde.",
                                      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "faire_virement", "description": "Vire de l'argent.",
                                      "parameters": {"type": "object", "required": ["beneficiaire", "montant"],
                                                     "properties": {"beneficiaire": {"type": "string",
                                                                                     "description": "Le nom."},
                                                                    "montant": {"type": "number"}}}}},
]  # fmt: skip


def test_les_outils_sont_decrits_dans_le_prompt_avec_leurs_parametres():
    assert outils_en_texte(DESCRIPTIONS) == (
        "- consulter_solde : Donne le solde. Paramètres : aucun.\n"
        "- faire_virement : Vire de l'argent. Paramètres : beneficiaire (Le nom.), montant."
    )


def test_le_json_du_modele_devient_des_appels_d_outils():
    texte = '{"appels": [{"outil": "faire_virement", "arguments": {"beneficiaire": "Fatima", "montant": 200}}]}'

    assert appels_du_json(texte) == (
        [{"name": "faire_virement", "args": {"beneficiaire": "Fatima", "montant": 200}}],
        True,
    )
    assert appels_du_json('{"appels": []}') == ([], True)


def test_un_json_coupe_compte_comme_aucun_outil_et_se_signale():
    assert appels_du_json('{"appels": [{"outil": "consulter_') == ([], False)


def test_l_historique_montre_les_appels_passes_en_json():
    passe = [HumanMessage("chhal f compte"), AIMessage("…", additional_kwargs={"outil": "consulter_solde"}),
             HumanMessage("w les factures ?")]  # fmt: skip

    lus = historique_json(passe)

    assert [type(m).__name__ for m in lus] == ["HumanMessage", "AIMessage", "HumanMessage"]
    assert lus[1].content == '{"appels": [{"outil": "consulter_solde", "arguments": {}}]}'
