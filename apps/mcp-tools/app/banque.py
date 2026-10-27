"""Appels à bank-api. Chaque fonction reçoit le client de la requête MCP (en-tête X-Client-Id), jamais un argument
choisi par le LLM."""

import os
from decimal import Decimal

import httpx

BANK_API_URL = os.environ.get("BANK_API_URL", "http://127.0.0.1:8000")


class RefusBanque(Exception):
    """La banque refuse l'opération (409). detail : {"code", "message", montants…} (voir bank-api/app/operations.py)."""

    def __init__(self, detail: dict):
        super().__init__(detail.get("message", "Refus de la banque"))
        self.detail = detail


def _get(client_id: int, chemin: str, **params):
    reponse = httpx.get(f"{BANK_API_URL}{chemin}", params=params, headers={"X-Client-Id": str(client_id)}, timeout=10)
    reponse.raise_for_status()  # une erreur 4xx ou 5xx devient une exception
    return reponse.json()


def _post(client_id: int, chemin: str, simulation: bool, json: dict | None = None) -> dict:
    reponse = httpx.post(
        f"{BANK_API_URL}{chemin}",
        params={"simulation": "true"} if simulation else None,
        json=json,
        headers={"X-Client-Id": str(client_id)},
        timeout=10,
    )
    if reponse.status_code == 409:
        raise RefusBanque(reponse.json()["detail"])
    reponse.raise_for_status()
    return reponse.json()


def _compte_principal(client_id: int) -> int:
    """Dans la Banque Atlas Démo, chaque client a un seul compte."""
    return _get(client_id, f"/clients/{client_id}/comptes")[0]["id"]


def solde(client_id: int) -> dict:
    return _get(client_id, f"/comptes/{_compte_principal(client_id)}/solde")


def transactions(client_id: int, limite: int = 5) -> list[dict]:
    return _get(client_id, f"/comptes/{_compte_principal(client_id)}/transactions", limite=limite)


def factures_impayees(client_id: int) -> list[dict]:
    return [f for f in _get(client_id, f"/clients/{client_id}/factures") if f["statut"] == "impayee"]


def beneficiaires(client_id: int) -> list[dict]:
    return _get(client_id, f"/clients/{client_id}/beneficiaires")


# Opérations. simulation=True : vérification à blanc, la banque vérifie et calcule tout puis annule.
def payer(client_id: int, facture_id: int, simulation: bool) -> dict:
    return _post(client_id, f"/factures/{facture_id}/payer", simulation)


def virer(client_id: int, beneficiaire_id: int, montant: Decimal, simulation: bool) -> dict:
    return _post(
        client_id, "/virements", simulation, json={"beneficiaire_id": beneficiaire_id, "montant": str(montant)}
    )
