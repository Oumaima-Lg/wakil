"""Appels à bank-api. Équivalent Spring : un RestClient (ou un client Feign).

Chaque fonction reçoit le client_id de la session : il n'est jamais choisi par le LLM.
"""

import os

import httpx

BANK_API_URL = os.environ.get("BANK_API_URL", "http://127.0.0.1:8000")


def _get(client_id: int, chemin: str, **params):
    reponse = httpx.get(
        f"{BANK_API_URL}{chemin}",
        params=params,
        headers={"X-Client-Id": str(client_id)},
        timeout=10,
    )
    reponse.raise_for_status()  # une erreur 4xx ou 5xx devient une exception
    return reponse.json()


def _compte_principal(client_id: int) -> int:
    """Dans la Banque Atlas Démo, chaque client a un seul compte."""
    return _get(client_id, f"/clients/{client_id}/comptes")[0]["id"]


def solde(client_id: int) -> dict:
    return _get(client_id, f"/comptes/{_compte_principal(client_id)}/solde")


def transactions(client_id: int) -> list[dict]:
    return _get(client_id, f"/comptes/{_compte_principal(client_id)}/transactions", limite=5)


def factures_impayees(client_id: int) -> list[dict]:
    factures = _get(client_id, f"/clients/{client_id}/factures")
    return [f for f in factures if f["statut"] == "impayee"]
