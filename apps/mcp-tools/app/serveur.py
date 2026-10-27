"""Serveur MCP de la Banque Atlas Démo : les outils de Wakil, utilisables par tout client MCP.

Ce fichier ne fait que le branchement MCP (noms, descriptions et annotations des outils, client, confirmation) ; le
déroulé d'un paiement ou d'un virement est dans operations.py.

Lancer (depuis apps/mcp-tools, bank-api démarrée) : uv run --env-file ../../.env uvicorn app.serveur:app --port 8002
Voir les outils dans l'inspecteur MCP officiel (télécharge un paquet Node) :
  uv run --with "mcp[cli]" mcp dev app/serveur.py:serveur
L'inspecteur passe alors par stdio, sans en-tête HTTP : il liste les outils, mais les appeler répond « l'en-tête
X-Client-Id manque ». Pour les appeler, s'y connecter en HTTP (http://127.0.0.1:8002/mcp) avec cet en-tête.

Deux règles de sécurité, valables pour n'importe quel client MCP (pas seulement Wakil) :
- le client vient de l'en-tête HTTP X-Client-Id de la requête, jamais d'un argument que le LLM pourrait choisir ;
  à durcir en S5 (jeton signé) et S6 (serveur joignable seulement par agent-api) ;
- un outil qui déplace de l'argent ne l'exécute que si l'appel porte la confirmation du client dans son _meta
  (« wakil/confirmation »). Sans elle, il ne fait qu'une vérification à blanc : rien ne bouge.
"""

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from app import banque, operations

serveur = MCPServer(
    "banque-atlas-demo",
    instructions="Outils de la Banque Atlas Démo (banque fictive) pour l'assistant Wakil. Données 100 % fictives.",
)

# Les annotations disent au client ce que fait l'outil. Un client bien fait demande l'accord de l'humain avant un
# outil « destructive » ; l'agent Wakil, lui, n'accepte que des outils dont les annotations correspondent à ce qu'il
# attend (voir agent-api/app/outils.py).
LECTURE = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
OPERATION = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False)
CONFIRMATION = "wakil/confirmation"


def client_de(ctx: Context) -> int:
    """Le client connecté, d'après l'en-tête que pose agent-api (qui le tient de la session du navigateur)."""
    valeur = (ctx.headers or {}).get("x-client-id", "")
    if not valeur.isdigit():
        raise ToolError("Client inconnu : l'en-tête X-Client-Id manque")
    return int(valeur)


def confirme(ctx: Context) -> bool:
    """Vrai seulement si l'application a joint la confirmation du client à cet appel."""
    meta = ctx.request_context.meta or {}
    return meta.get(CONFIRMATION) == "oui"


@serveur.tool(title="Consulter le solde", annotations=LECTURE, structured_output=True)
def consulter_solde(ctx: Context) -> dict[str, Any]:
    """Donne le solde actuel du compte du client."""
    return banque.solde(client_de(ctx))


@serveur.tool(title="Dernières opérations", annotations=LECTURE, structured_output=True)
def lister_transactions(ctx: Context) -> dict[str, Any]:
    """Liste les dernières opérations du compte du client (dépenses, virements reçus)."""
    return {"transactions": banque.transactions(client_de(ctx))}


@serveur.tool(title="Factures à payer", annotations=LECTURE, structured_output=True)
def lister_factures(ctx: Context) -> dict[str, Any]:
    """Montre les factures impayées du client, sans rien payer."""
    return {"factures": banque.factures_impayees(client_de(ctx))}


@serveur.tool(title="Payer une facture", annotations=OPERATION, structured_output=True)
def payer_facture(
    ctx: Context,
    fournisseur: Annotated[
        Literal["eau_electricite", "internet", "mobile"] | None,
        Field(description="eau_electricite pour l'eau ou l'électricité, internet, ou mobile (téléphone)."),
    ] = None,
    facture_id: Annotated[
        int | None, Field(description="Identifiant exact de la facture, donné par l'application : jamais à deviner.")
    ] = None,
) -> dict[str, Any]:
    """Paye une facture impayée du client (eau et électricité, internet, mobile). En darija, le client dit
    « khelless », « khalles », « nkhelless » ou « خلص ». Sans la confirmation du client, l'outil vérifie seulement :
    rien n'est payé."""
    return operations.payer_facture(client_de(ctx), fournisseur, facture_id, confirme(ctx))


@serveur.tool(title="Faire un virement", annotations=OPERATION, structured_output=True)
def faire_virement(
    ctx: Context,
    beneficiaire: Annotated[str | None, Field(description="Le prénom ou le nom du bénéficiaire, tel qu'écrit.")] = None,
    montant: Annotated[float | str | None, Field(description="Le montant en dirhams (DH).")] = None,
    beneficiaire_id: Annotated[
        int | None, Field(description="Identifiant exact du bénéficiaire, donné par l'application : jamais à deviner.")
    ] = None,
) -> dict[str, Any]:
    """Vire de l'argent à un bénéficiaire déjà enregistré par le client. En darija, le client dit « sifet », « sift »,
    « 7awel » ou « صيفط ». Sans la confirmation du client, l'outil vérifie seulement : rien n'est viré."""
    return operations.faire_virement(client_de(ctx), beneficiaire, montant, beneficiaire_id, confirme(ctx))


# L'application web (ASGI) que lance uvicorn. Sans état (spécification MCP 2026-07-28) : chaque requête se suffit à
# elle-même, plusieurs copies du serveur peuvent tourner côte à côte (Azure Container Apps, S6).
app = serveur.streamable_http_app(stateless_http=True, json_response=True)
