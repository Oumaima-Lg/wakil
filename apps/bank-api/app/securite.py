from typing import Annotated

from fastapi import Depends, Header


def client_connecte(x_client_id: Annotated[int, Header()]) -> int:
    """Identifiant du client connecté, lu dans l'en-tête HTTP « X-Client-Id ».

    Provisoire (S1) : cet en-tête est posé par le code de l'agent, jamais par le LLM.
    Il sera remplacé par la vérification d'un jeton signé (JWT).
    """
    return x_client_id


# Raccourci à mettre dans la signature d'une route pour recevoir l'id du client connecté.
ClientConnecte = Annotated[int, Depends(client_connecte)]
