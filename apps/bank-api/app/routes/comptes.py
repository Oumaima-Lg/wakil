"""Routes des comptes. Équivalent Spring : un @RestController avec @RequestMapping("/comptes")."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.db import Connexion
from app.schemas import Solde, Transaction
from app.securite import ClientConnecte

router = APIRouter(prefix="/comptes", tags=["Comptes"])


def compte_du_client(conn, compte_id: int, client_id: int):
    """Renvoie le compte s'il appartient au client connecté, sinon répond 404."""
    compte = conn.execute(
        "SELECT id, solde FROM comptes WHERE id = %s AND client_id = %s",
        (compte_id, client_id),
    ).fetchone()
    if compte is None:
        # 404 et pas 403 : on ne révèle pas qu'un compte existe chez un autre client.
        raise HTTPException(status_code=404, detail="Compte introuvable")
    return compte


@router.get("/{compte_id}/solde")
def consulter_solde(compte_id: int, client_id: ClientConnecte, conn: Connexion) -> Solde:
    """Solde actuel d'un compte du client connecté."""
    compte = compte_du_client(conn, compte_id, client_id)
    return Solde(compte_id=compte["id"], solde=compte["solde"])


@router.get("/{compte_id}/transactions")
def lister_transactions(
    compte_id: int,
    client_id: ClientConnecte,
    conn: Connexion,
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[Transaction]:
    """Dernières opérations d'un compte du client connecté, de la plus récente à la plus ancienne."""
    compte_du_client(conn, compte_id, client_id)
    lignes = conn.execute(
        "SELECT id, date, montant, libelle FROM transactions"
        " WHERE compte_id = %s ORDER BY date DESC, id DESC LIMIT %s",
        (compte_id, limite),
    ).fetchall()
    return [Transaction(**ligne) for ligne in lignes]
