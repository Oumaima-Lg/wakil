"""L'écran d'accueil et l'espace bancaire : ce que les pages affichent, lu en direct dans la banque. Lecture seule."""

from decimal import Decimal

from fastapi import APIRouter

from app import banque
from app.session import CLIENTS_DEMO, ClientConnecte

router = APIRouter(tags=["espace"])


def resume_client(client_id: int, scenario: str) -> dict:
    compte = banque.compte(client_id)
    factures = banque.factures_impayees(client_id)
    return {
        **banque.profil(client_id),
        "scenario": scenario,
        "solde": compte["solde"],
        "plafond_virement": compte["plafond_virement"],
        "factures_a_payer": len(factures),
        "total_a_payer": str(sum((Decimal(f["montant"]) for f in factures), Decimal("0.00"))),
    }


@router.get("/clients-demo")
def clients_demo() -> list[dict]:
    """Les clients proposés sur l'écran d'accueil, avec un résumé de leur compte lu en direct dans la banque."""
    return [resume_client(client_id, scenario) for client_id, scenario in CLIENTS_DEMO.items()]


@router.get("/moi/espace")
def mon_espace(client_id: ClientConnecte) -> dict:
    """Tout ce que l'espace bancaire affiche, en un seul appel (« backend for frontend »)."""
    return {
        "profil": banque.profil(client_id),
        "compte": banque.compte(client_id),
        "operations": banque.operations(client_id),
        "factures": banque.toutes_factures(client_id),
        "beneficiaires": banque.beneficiaires(client_id),
    }
