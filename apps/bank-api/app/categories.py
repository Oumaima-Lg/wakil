"""Les catégories de dépenses de la Banque Atlas Démo, reconnues au début du libellé de l'opération.

Une vraie banque range chaque opération dans une catégorie (souvent d'après le code du commerçant) ; la banque fictive
n'a que des libellés génériques (voir data/seed), qu'il suffit de reconnaître.
"""

# Début du libellé → (code, nom affiché). Les codes sont ceux que le serveur MCP propose au LLM.
CATEGORIES = {
    "Courses supermarché": ("courses", "Courses"),
    "Retrait guichet automatique": ("retraits", "Retraits"),
    "Restaurant": ("restaurant", "Restaurant"),
    "Café": ("cafe", "Café"),
    "Pharmacie": ("pharmacie", "Pharmacie"),
    "Taxi": ("taxi", "Taxi"),
    "Carburant": ("carburant", "Carburant"),
    "Vêtements": ("vetements", "Vêtements"),
    "Paiement facture": ("factures", "Factures"),
    "Virement vers": ("virements", "Virements envoyés"),
}
AUTRES = ("autres", "Autres")


def categorie(libelle: str) -> tuple[str, str]:
    """(code, nom affiché) de la catégorie d'une opération."""
    for debut, trouvee in CATEGORIES.items():
        if libelle.startswith(debut):
            return trouvee
    return AUTRES
