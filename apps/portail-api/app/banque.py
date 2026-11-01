"""Appels à bank-api pour les pages de l'espace bancaire et l'écran d'accueil : des lectures, et les actions sur la
carte (bloquer, débloquer, faire opposition, commander une nouvelle carte).

Équivalent Spring : un RestClient (ou un client Feign). L'IA, elle, ne passe jamais par ici : ses outils sont dans le
serveur MCP (apps/mcp-tools). Chaque fonction reçoit le client_id de la session ; bank-api reçoit un jeton de 60
secondes signé par portail-api pour ce client (voir session.jeton_pour_la_banque).
"""

import os

import httpx

from app.session import jeton_pour_la_banque

BANK_API_URL = os.environ.get("BANK_API_URL", "http://127.0.0.1:8000")


def _entetes(client_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {jeton_pour_la_banque(client_id)}"}


def _get(client_id: int, chemin: str, **params):
    reponse = httpx.get(f"{BANK_API_URL}{chemin}", params=params, headers=_entetes(client_id), timeout=10)
    reponse.raise_for_status()  # une erreur 4xx ou 5xx devient une exception
    return reponse.json()


class RefusBanque(Exception):
    """La banque refuse (409, avec un code) ou ne trouve pas (404) : son statut et son détail, transmis au front."""

    def __init__(self, statut: int, detail):
        super().__init__(str(detail))
        self.statut, self.detail = statut, detail


def _post(client_id: int, chemin: str, json: dict | None = None) -> dict:
    reponse = httpx.post(f"{BANK_API_URL}{chemin}", json=json, headers=_entetes(client_id), timeout=10)
    if reponse.status_code in (404, 409):
        raise RefusBanque(reponse.status_code, reponse.json()["detail"])
    reponse.raise_for_status()
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


def factures_impayees(client_id: int) -> list[dict]:
    factures = _get(client_id, f"/clients/{client_id}/factures")
    return [f for f in factures if f["statut"] == "impayee"]


def operations(client_id: int, limite: int = 50) -> list[dict]:
    return _get(client_id, f"/comptes/{_compte_principal(client_id)}/transactions", limite=limite)


def toutes_factures(client_id: int) -> list[dict]:
    return _get(client_id, f"/clients/{client_id}/factures")


def beneficiaires(client_id: int) -> list[dict]:
    return _get(client_id, f"/clients/{client_id}/beneficiaires")


def cartes(client_id: int) -> list[dict]:
    """Les cartes du client et leur état (active, bloquée, en opposition) : la page « Ma carte » les affiche."""
    return _get(client_id, f"/clients/{client_id}/cartes")


def debloquer_carte(client_id: int, carte_id: int) -> dict:
    return _post(client_id, f"/cartes/{carte_id}/deblocage")


def faire_opposition(client_id: int, carte_id: int, motif: str) -> dict:
    return _post(client_id, f"/cartes/{carte_id}/opposition", json={"motif": motif})


def remplacer_carte(client_id: int, carte_id: int) -> dict:
    return _post(client_id, f"/cartes/{carte_id}/remplacement")


def bloquer_carte(client_id: int, carte_id: int) -> dict:
    return _post(client_id, f"/cartes/{carte_id}/blocage")
