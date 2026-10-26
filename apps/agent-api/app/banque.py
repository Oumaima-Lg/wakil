"""Appels à bank-api. Équivalent Spring : un RestClient (ou un client Feign).

Chaque fonction reçoit le client_id de la session : il n'est jamais choisi par le LLM.
"""

import os
from decimal import Decimal

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


def profil(client_id: int) -> dict:
    return _get(client_id, f"/clients/{client_id}")


def compte(client_id: int) -> dict:
    """Le compte du client (id, RIB masqué, plafond de virement) avec son solde."""
    infos = _get(client_id, f"/clients/{client_id}/comptes")[0]
    return {**infos, "solde": _get(client_id, f"/comptes/{infos['id']}/solde")["solde"]}


def solde(client_id: int) -> dict:
    return _get(client_id, f"/comptes/{_compte_principal(client_id)}/solde")


def transactions(client_id: int) -> list[dict]:
    return _get(client_id, f"/comptes/{_compte_principal(client_id)}/transactions", limite=5)


def factures_impayees(client_id: int) -> list[dict]:
    factures = _get(client_id, f"/clients/{client_id}/factures")
    return [f for f in factures if f["statut"] == "impayee"]


class RefusBanque(Exception):
    """La banque refuse l'opération (409). detail : {"code", "message", montants…} (voir bank-api/app/operations.py)."""

    def __init__(self, detail: dict):
        super().__init__(detail.get("message", "Refus de la banque"))
        self.detail = detail


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


# Opérations. simulation=True : vérification à blanc, la banque vérifie et calcule tout puis annule.
def payer(client_id: int, facture_id: int, simulation: bool = False) -> dict:
    return _post(client_id, f"/factures/{facture_id}/payer", simulation)


def virer(client_id: int, beneficiaire_id: int, montant: Decimal, simulation: bool = False) -> dict:
    return _post(
        client_id, "/virements", simulation, json={"beneficiaire_id": beneficiaire_id, "montant": str(montant)}
    )


# Lectures pour l'espace bancaire du front (pas des outils du LLM).
def operations(client_id: int, limite: int = 50) -> list[dict]:
    return _get(client_id, f"/comptes/{_compte_principal(client_id)}/transactions", limite=limite)


def toutes_factures(client_id: int) -> list[dict]:
    return _get(client_id, f"/clients/{client_id}/factures")


def beneficiaires(client_id: int) -> list[dict]:
    return _get(client_id, f"/clients/{client_id}/beneficiaires")
