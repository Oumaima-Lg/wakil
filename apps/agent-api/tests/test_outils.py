"""Ce que l'agent accepte du serveur MCP : une liste fermée d'outils, aux annotations attendues, au schéma simplifié."""

from types import SimpleNamespace

from app import outils

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
    monkeypatch.setattr(
        outils,
        "_lister",
        lambda: [
            outil("consulter_solde", lecture=True),
            outil("payer_facture", destructif=True, schema=SCHEMA_PAIEMENT),
            outil("envoyer_email", lecture=True),  # inconnu de l'agent : liste fermée
            outil("lister_factures", destructif=True),  # se dit destructif alors qu'il doit seulement lire
            outil("faire_virement", lecture=True),  # déplace de l'argent mais se dit « lecture » : piège
        ],
    )

    noms = [d["function"]["name"] for d in outils.descriptions_pour_le_llm({"consulter_solde", "lister_factures"},
                                                                           {"payer_facture", "faire_virement"})]  # fmt: skip

    assert noms == ["consulter_solde", "payer_facture"]
