"""Les outils de la banque, à travers le serveur MCP (apps/mcp-tools) : l'agent est un client MCP.

Le client voyage dans l'en-tête X-Client-Id (jamais dans les arguments, que le LLM pourrait choisir) et la
confirmation du client dans le _meta de l'appel : sans elle, le serveur ne fait qu'une vérification à blanc.
"""

import asyncio
import logging
import os

from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

MCP_TOOLS_URL = os.environ.get("MCP_TOOLS_URL", "http://127.0.0.1:8002/mcp")
CONFIRMATION = "wakil/confirmation"

journal = logging.getLogger(__name__)


class RefusOutil(Exception):
    """Le serveur (ou la banque derrière lui) refuse : detail = {"code", "message", …} (facture absente, solde…)."""

    def __init__(self, detail: dict):
        super().__init__(detail.get("message", "Refus"))
        self.detail = detail


class OutilsIndisponibles(Exception):
    """Le serveur MCP, ou la banque derrière lui, ne répond pas."""


def _client(client_id: int | None) -> Client:
    entetes = {"X-Client-Id": str(client_id)} if client_id is not None else {}
    return Client(streamable_http_client(MCP_TOOLS_URL, http_client=create_mcp_http_client(headers=entetes)))


def appeler(client_id: int, nom: str, arguments: dict, confirme: bool = False) -> dict:
    """Appelle un outil (tools/call). confirme : le client a dit « oui » à la carte, l'opération est exécutée."""

    async def faire():
        async with _client(client_id) as client:
            return await client.call_tool(nom, arguments, meta={CONFIRMATION: "oui"} if confirme else None)

    try:
        # Le SDK MCP est asynchrone, le graphe tourne dans un fil à part : une boucle le temps de l'appel.
        resultat = asyncio.run(faire())
    except Exception as panne:  # serveur MCP arrêté, réseau coupé…
        raise OutilsIndisponibles(str(panne)) from panne
    if resultat.is_error:
        raise OutilsIndisponibles(" ".join(getattr(c, "text", "") for c in resultat.content))
    donnees = resultat.structured_content or {}
    if "refus" in donnees:
        raise RefusOutil(donnees["refus"])
    return donnees


def _lister() -> list:
    async def faire():
        async with _client(None) as client:
            return (await client.list_tools()).tools

    return asyncio.run(faire())


def schema_pour_le_llm(schema: dict) -> dict:
    """Le schéma d'un outil, simplifié pour le LLM : sans les identifiants (« …_id » : donnés par l'application,
    jamais devinés), sans les « ou rien » (null), et chaque paramètre restant devient obligatoire."""
    proprietes = {}
    for nom, propriete in schema.get("properties", {}).items():
        if nom.endswith("_id"):
            continue
        choix = [p for p in propriete.get("anyOf", [propriete]) if p.get("type") != "null"]
        simple = {cle: valeur for cle, valeur in choix[0].items() if cle != "title"} if choix else {}
        if "description" in propriete:
            simple["description"] = propriete["description"]
        proprietes[nom] = simple
    return {"type": "object", "properties": proprietes, "required": list(proprietes)}


def descriptions_pour_le_llm(lectures: set[str], operations: set[str]) -> list[dict]:
    """Les outils annoncés par le serveur MCP (tools/list), au format que comprend le LLM.

    Liste fermée : seulement les outils que l'agent connaît, et seulement si leurs annotations disent ce qu'il attend
    (lecture : readOnlyHint ; opération : destructiveHint, donc confirmation obligatoire). Un serveur qui ferait
    passer un outil de lecture pour un outil qui déplace de l'argent (« rug pull ») le verrait simplement retiré.
    """
    descriptions = []
    for outil in _lister():
        annotations = outil.annotations
        attendu = (outil.name in lectures and annotations is not None and annotations.read_only_hint) or (
            outil.name in operations and annotations is not None and annotations.destructive_hint
        )
        if not attendu:
            journal.warning("Outil MCP ignoré : %s (inconnu de l'agent, ou annotations inattendues)", outil.name)
            continue
        descriptions.append(
            {
                "type": "function",
                "function": {
                    "name": outil.name,
                    "description": outil.description,
                    "parameters": schema_pour_le_llm(outil.input_schema),
                },
            }
        )
    return descriptions
