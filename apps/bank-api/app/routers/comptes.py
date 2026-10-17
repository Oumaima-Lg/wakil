from typing import Annotated

from fastapi import APIRouter, Query

from app.db import Connexion
from app.schemas import Solde, Transaction
from app.securite import CompteDuClient

router = APIRouter(prefix="/comptes", tags=["Comptes"])


@router.get("/{compte_id}/solde")
def consulter_solde(compte: CompteDuClient) -> Solde:
    """Solde actuel d'un compte du client connecté."""
    return Solde(compte_id=compte["id"], solde=compte["solde"])


@router.get("/{compte_id}/transactions")
def lister_transactions(
    compte: CompteDuClient,
    conn: Connexion,
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[Transaction]:
    """Dernières opérations d'un compte du client connecté, de la plus récente à la plus ancienne."""
    lignes = conn.execute(
        "SELECT id, date, montant, libelle FROM transactions WHERE compte_id = %s ORDER BY date DESC, id DESC LIMIT %s",
        (compte["id"], limite),
    ).fetchall()
    return [Transaction(**ligne) for ligne in lignes]
