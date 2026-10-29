"""Ce que l'agent accepte du serveur MCP : une liste fermée d'outils, aux annotations attendues, au schéma simplifié."""

from types import SimpleNamespace

from app import agent, outils

# Le schéma tel que le serveur MCP l'annonce pour payer_facture (paramètres facultatifs : « ou null »)
SCHEMA_PAIEMENT = {
    "type": "object",
    "properties": {
        "fournisseur": {
            "anyOf": [{"enum": ["eau_electricite", "internet", "mobile"], "type": "string"}, {"type": "null"}],
            "default": None,
            "description": "eau_electricite pour l'eau ou l'électricité, internet, ou mobile (téléphone).",
            "title": "Fournisseur",
        },
        "facture_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": None, "title": "Facture Id"},
    },
}


# Le schéma que le serveur MCP de la FAQ annonce pour question_faq
SCHEMA_FAQ = {
    "type": "object",
    "properties": {"question": {"type": "string", "description": "La phrase du client, telle qu'il l'a écrite."}},
    "required": ["question"],
}


def outil(nom, lecture=False, destructif=False, schema=None):
    annotations = SimpleNamespace(read_only_hint=lecture, destructive_hint=destructif)
    return SimpleNamespace(
        name=nom, description=f"Description de {nom}", input_schema=schema or {}, annotations=annotations
    )


def test_le_llm_ne_voit_ni_les_identifiants_ni_les_null():
    assert outils.schema_pour_le_llm(SCHEMA_PAIEMENT) == {
        "type": "object",
        "properties": {
            "fournisseur": {
                "enum": ["eau_electricite", "internet", "mobile"],
                "type": "string",
                "description": "eau_electricite pour l'eau ou l'électricité, internet, ou mobile (téléphone).",
            }
        },
        "required": ["fournisseur"],  # facture_id n'est jamais à deviner : seul le bouton du front le donne
    }


def test_un_montant_nombre_ou_texte_devient_un_nombre_pour_le_llm():
    schema = {"properties": {"montant": {"anyOf": [{"type": "number"}, {"type": "string"}, {"type": "null"}]}}}
    assert outils.schema_pour_le_llm(schema)["properties"]["montant"] == {"type": "number"}


def test_seuls_les_outils_connus_aux_annotations_attendues_sont_donnes_au_llm(monkeypatch):
    banque, faq = outils.MCP_TOOLS_URL, outils.MCP_FAQ_URL
    monkeypatch.setattr(
        outils,
        "_lister",
        lambda: (
            [
                (banque, outil("consulter_solde", lecture=True)),
                (banque, outil("payer_facture", destructif=True, schema=SCHEMA_PAIEMENT)),
                (banque, outil("envoyer_email", lecture=True)),  # inconnu de l'agent : liste fermée
                (banque, outil("lister_factures", destructif=True)),  # se dit destructif, doit seulement lire
                (banque, outil("faire_virement", lecture=True)),  # déplace de l'argent mais se dit « lecture » : piège
                (faq, outil("question_faq", lecture=True, schema=SCHEMA_FAQ)),
                (faq, outil("faire_virement", destructif=True)),  # la FAQ annonce un outil de la banque : piège
            ],
            True,
        ),
    )

    descriptions, complet = outils.descriptions_pour_le_llm({"consulter_solde", "lister_factures", "question_faq"},
                                                            {"payer_facture", "faire_virement"})  # fmt: skip

    assert [d["function"]["name"] for d in descriptions] == ["consulter_solde", "payer_facture", "question_faq"]
    assert complet


def test_le_llm_ne_voit_pas_la_question_que_remplit_l_application():
    """Pour la FAQ, on cherche avec la phrase du client : le LLM ne peut pas la reformuler."""
    schema = outils.schema_pour_le_llm(SCHEMA_FAQ, outils.REMPLIS_PAR_L_APPLICATION["question_faq"])

    assert schema == {"type": "object", "properties": {}, "required": []}


def test_le_client_n_est_dit_qu_au_serveur_de_la_banque():
    assert outils._entetes(outils.MCP_TOOLS_URL, 1) == {"X-Client-Id": "1"}
    assert outils._entetes(outils.MCP_FAQ_URL, 1) == {}


def test_chaque_outil_connu_a_son_serveur():
    assert set(outils.SERVEUR_DE) == {*agent.OUTILS, *agent.OPERATIONS, agent.OUTIL_FAQ}
