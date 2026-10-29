"""Serveur MCP de la FAQ de la Banque Atlas Démo : un seul outil, question_faq, en lecture seule.

Ce fichier ne fait que le branchement MCP (nom, description et annotations de l'outil) ; la recherche est dans faq.py.

Lancer (depuis apps/rag-faq, base et Ollama démarrés, FAQ indexée) :
  uv run --env-file ../../.env uvicorn app.serveur:app --port 8004

La FAQ est publique : le serveur ne demande pas qui est le client, et agent-api ne le lui dit pas (minimisation des
données). Il ne rédige rien : il renvoie la fiche telle qu'elle est écrite, et c'est l'agent qui la cite.
"""

from dataclasses import asdict
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from app import faq

serveur = MCPServer(
    "faq-banque-atlas-demo",
    instructions="FAQ de la Banque Atlas Démo (banque fictive) pour l'assistant Wakil. Données 100 % fictives.",
)

LECTURE = ToolAnnotations(readOnlyHint=True, openWorldHint=False)


@serveur.tool(title="Question générale sur la banque", annotations=LECTURE, structured_output=True)
def question_faq(
    question: Annotated[
        str,
        Field(description="La phrase du client, telle qu'il l'a écrite : donnée par l'application, jamais reformulée."),
    ],
) -> dict[str, Any]:
    """Répond aux questions générales sur la Banque Atlas Démo et sur Wakil : frais et tarifs, plafond et délai des
    virements, bénéficiaires, carte perdue ou volée, codes et sécurité, découvert, données, horaires. Pas pour le compte
    du client (solde, opérations, factures à payer), ni pour payer ou virer."""
    try:
        trouvaille = faq.chercher(question)
    except faq.FaqIndisponible as panne:
        raise ToolError(f"FAQ indisponible : {panne}") from panne
    # Sous le seuil, aucune fiche : l'agent le dit au lieu d'en citer une qui ne répond pas.
    return {"fiche": asdict(trouvaille) if trouvaille else None}


# L'application web (ASGI) que lance uvicorn, sans état comme le serveur de la banque (apps/mcp-tools).
app = serveur.streamable_http_app(stateless_http=True, json_response=True)
