"""Les outils de Wakil, à travers deux serveurs MCP : l'agent est un client MCP.

- apps/mcp-tools : les outils de la banque (solde, opérations, factures, paiement, virement) ;
- apps/rag-faq : la FAQ (question_faq), qui retrouve la fiche qui répond.

Le client voyage dans l'en-tête X-Client-Id (jamais dans les arguments, que le LLM pourrait choisir), et seulement vers
le serveur de la banque : la FAQ est publique et n'a pas à savoir qui demande. La confirmation du client voyage dans le
_meta de l'appel : sans elle, le serveur de la banque ne fait qu'une vérification à blanc.
"""

import asyncio
import logging
import os

from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

MCP_TOOLS_URL = os.environ.get("MCP_TOOLS_URL", "http://127.0.0.1:8002/mcp")  # la banque
MCP_FAQ_URL = os.environ.get("MCP_FAQ_URL", "http://127.0.0.1:8004/mcp")  # la FAQ
CONFIRMATION = "wakil/confirmation"

# Chaque outil n'est accepté que de son serveur : un serveur qui annoncerait l'outil d'un autre (la FAQ qui
# proposerait faire_virement) serait ignoré.
SERVEUR_DE = {
    **dict.fromkeys(
        [
            "consulter_solde",
            "consulter_plafond",
            "lister_transactions",
            "lister_factures",
            "lister_beneficiaires",
            "analyser_depenses",
            "payer_facture",
            "faire_virement",
        ],
        MCP_TOOLS_URL,
    ),
    "question_faq": MCP_FAQ_URL,
}
# Les paramètres que l'application remplit elle-même, cachés au LLM (en plus des « …_id ») : pour la FAQ, on cherche
# avec la phrase du client, jamais avec une reformulation du LLM.
REMPLIS_PAR_L_APPLICATION = {"question_faq": {"question"}}
# Les paramètres que le LLM peut laisser vides : tous les autres lui sont présentés comme obligatoires, sinon un petit
# modèle les oublie. Le montant d'une facture ne sert que si le client la désigne ainsi (« la facture de 249 DH ») ;
# la catégorie des dépenses, que s'il en nomme une (« chhal srefti f restaurant »).
OPTIONNELS_POUR_LE_LLM = {"payer_facture": {"montant"}, "analyser_depenses": {"categorie"}}

journal = logging.getLogger(__name__)


class RefusOutil(Exception):
    """Le serveur (ou la banque derrière lui) refuse : detail = {"code", "message", …} (facture absente, solde…)."""

    def __init__(self, detail: dict):
        super().__init__(detail.get("message", "Refus"))
        self.detail = detail


class OutilsIndisponibles(Exception):
    """Un serveur MCP, ou la banque derrière lui, ne répond pas."""


def _entetes(url: str, client_id: int | None) -> dict[str, str]:
    """Le client n'est dit qu'au serveur de la banque (minimisation des données)."""
    return {"X-Client-Id": str(client_id)} if url == MCP_TOOLS_URL and client_id is not None else {}


def _client(url: str, client_id: int | None) -> Client:
    return Client(streamable_http_client(url, http_client=create_mcp_http_client(headers=_entetes(url, client_id))))


def appeler(client_id: int | None, nom: str, arguments: dict, confirme: bool = False) -> dict:
    """Appelle un outil (tools/call) sur son serveur. confirme : le client a dit « oui » à la carte, l'opération est
    exécutée."""

    async def faire():
        async with _client(SERVEUR_DE[nom], client_id) as client:
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


def _lister() -> tuple[list[tuple[str, object]], bool]:
    """Les outils annoncés par chaque serveur (tools/list), avec l'adresse du serveur qui les annonce.

    Sans la banque, Wakil ne peut rien faire : l'erreur remonte. Sans la FAQ, il fonctionne quand même ; le booléen
    dit si la liste est complète.
    """

    async def lister(url):
        async with _client(url, None) as client:
            return (await client.list_tools()).tools

    annonces = [(MCP_TOOLS_URL, outil) for outil in asyncio.run(lister(MCP_TOOLS_URL))]
    try:
        annonces += [(MCP_FAQ_URL, outil) for outil in asyncio.run(lister(MCP_FAQ_URL))]
    except Exception:
        journal.warning("Serveur MCP de la FAQ injoignable : Wakil répond sans la FAQ pour l'instant")
        return annonces, False
    return annonces, True


def schema_pour_le_llm(
    schema: dict, caches: set[str] | frozenset[str] = frozenset(), optionnels: set[str] | frozenset[str] = frozenset()
) -> dict:
    """Le schéma d'un outil, simplifié pour le LLM : sans les identifiants (« …_id » : donnés par l'application,
    jamais devinés) ni les paramètres que l'application remplit (caches), sans les « ou rien » (null), et chaque
    paramètre restant devient obligatoire, sauf les optionnels."""
    proprietes = {}
    for nom, propriete in schema.get("properties", {}).items():
        if nom.endswith("_id") or nom in caches:
            continue
        choix = [p for p in propriete.get("anyOf", [propriete]) if p.get("type") != "null"]
        simple = {cle: valeur for cle, valeur in choix[0].items() if cle != "title"} if choix else {}
        if "description" in propriete:
            simple["description"] = propriete["description"]
        proprietes[nom] = simple
    return {
        "type": "object",
        "properties": proprietes,
        "required": [nom for nom in proprietes if nom not in optionnels],
    }


def descriptions_pour_le_llm(lectures: set[str], operations: set[str]) -> tuple[list[dict], bool]:
    """Les outils annoncés par les serveurs MCP (tools/list), au format que comprend le LLM, et si la liste est complète.

    Liste fermée : seulement les outils que l'agent connaît, venus de leur serveur, et seulement si leurs annotations
    disent ce qu'il attend (lecture : readOnlyHint ; opération : destructiveHint, donc confirmation obligatoire). Un
    serveur qui ferait passer un outil de lecture pour un outil qui déplace de l'argent (« rug pull »), ou qui
    annoncerait l'outil d'un autre serveur, le verrait simplement retiré.
    """
    annonces, complet = _lister()
    descriptions = []
    for url, outil in annonces:
        annotations = outil.annotations
        attendu = SERVEUR_DE.get(outil.name) == url and (
            (outil.name in lectures and annotations is not None and annotations.read_only_hint)
            or (outil.name in operations and annotations is not None and annotations.destructive_hint)
        )
        if not attendu:
            journal.warning("Outil MCP ignoré : %s (inconnu, venu d'un autre serveur, ou annotations inattendues)",
                            outil.name)  # fmt: skip
            continue
        descriptions.append(
            {
                "type": "function",
                "function": {
                    "name": outil.name,
                    "description": outil.description,  # telle que le serveur l'annonce, sans retouche
                    "parameters": schema_pour_le_llm(
                        outil.input_schema,
                        REMPLIS_PAR_L_APPLICATION.get(outil.name, set()),
                        OPTIONNELS_POUR_LE_LLM.get(outil.name, set()),
                    ),
                },
            }
        )
    return descriptions, complet
