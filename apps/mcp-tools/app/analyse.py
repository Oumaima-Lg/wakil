"""L'analyse des dépenses : le LLM choisit seulement le mois et la catégorie, la banque fait les calculs.

Aucun type MCP ici (serveur.py fait le branchement). Un petit modèle se trompe vite dans une addition : les totaux
viennent donc de bank-api, calculés sur toutes les opérations de la période.
"""

from datetime import date, datetime, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

from app import banque

MAROC = ZoneInfo("Africa/Casablanca")
Periode = Literal["ce_mois", "mois_dernier"]
# Les codes que la banque donne à ses catégories (voir bank-api/app/categories.py), et leur nom affiché.
CATEGORIES = {
    "courses": "Courses",
    "restaurant": "Restaurant",
    "cafe": "Café",
    "pharmacie": "Pharmacie",
    "taxi": "Taxi",
    "carburant": "Carburant",
    "vetements": "Vêtements",
    "retraits": "Retraits",
    "factures": "Factures",
    "virements": "Virements envoyés",
}
Categorie = Literal[
    "courses", "restaurant", "cafe", "pharmacie", "taxi", "carburant", "vetements", "retraits", "factures", "virements"
]


def dates(periode: Periode, aujourd_hui: date) -> tuple[date, date]:
    """Du 1er du mois à aujourd'hui (ce mois-ci), ou tout le mois d'avant."""
    debut_du_mois = aujourd_hui.replace(day=1)
    if periode == "ce_mois":
        return debut_du_mois, aujourd_hui
    fin = debut_du_mois - timedelta(days=1)
    return fin.replace(day=1), fin


def depenses(
    client_id: int, periode: Periode = "ce_mois", categorie: str | None = None, aujourd_hui: date | None = None
) -> dict[str, Any]:
    """Le résumé de la banque pour ce mois-là ; avec une catégorie, sa ligne (à zéro si rien n'y a été dépensé)."""
    du, au = dates(periode, aujourd_hui or datetime.now(MAROC).date())
    resume = banque.depenses(client_id, du, au)
    ligne = None
    if categorie in CATEGORIES:
        ligne = next(
            (c for c in resume["par_categorie"] if c["categorie"] == categorie),
            {"categorie": categorie, "nom": CATEGORIES[categorie], "total": "0.00", "nombre": 0},
        )
    return {"periode": periode, **resume, "categorie": ligne}
