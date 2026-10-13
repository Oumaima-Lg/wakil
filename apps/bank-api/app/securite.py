from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.db import Connexion


def client_connecte(x_client_id: Annotated[int, Header()]) -> int:
    """Identifiant du client connecté, lu dans l'en-tête HTTP « X-Client-Id ».

    Provisoire (S1) : cet en-tête est posé par le code de l'agent, jamais par le LLM.
    Il sera remplacé par la vérification d'un jeton signé (JWT).
    """
    return x_client_id


# Raccourci à mettre dans la signature d'une route pour recevoir l'id du client connecté.
ClientConnecte = Annotated[int, Depends(client_connecte)]


def compte_du_client(compte_id: int, client_id: ClientConnecte, conn: Connexion) -> dict:
    """Le compte {compte_id} de l'URL, s'il appartient au client connecté. Sinon : 404."""
    compte = conn.execute(
        "SELECT id, solde FROM comptes WHERE id = %s AND client_id = %s",
        (compte_id, client_id),
    ).fetchone()
    if compte is None:
        # 404 et pas 403 : on ne révèle pas qu'un compte existe chez un autre client.
        raise HTTPException(status_code=404, detail="Compte introuvable")
    return compte


# Une route qui déclare ce paramètre ne peut pas oublier le contrôle d'accès : FastAPI le fait avant elle.
CompteDuClient = Annotated[dict, Depends(compte_du_client)]
