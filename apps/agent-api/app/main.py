"""API de l'agent Wakil.

Lancer (depuis apps/agent-api, bank-api et Ollama démarrés) : uv run fastapi dev --port 8001
"""

import json
from typing import Annotated

from fastapi import FastAPI, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent import config, nouveau_tour, wakil

app = FastAPI(
    title="Wakil · agent",
    description="Agent bancaire en darija. **Données 100 % fictives – projet de démonstration.**",
)


class Message(BaseModel):
    conversation_id: str = Field(pattern=r"^[A-Za-z0-9-]{1,64}$")  # choisi par le navigateur (un UUID)
    texte: str = Field(min_length=1, max_length=500)  # limite la taille de ce qu'on envoie au LLM


def evenement(nom: str, donnees: dict) -> str:
    """Un événement SSE : une ligne « event: », une ligne « data: » en JSON, puis une ligne vide."""
    return f"event: {nom}\ndata: {json.dumps(donnees, ensure_ascii=False)}\n\n"


@app.post("/chat")
def chat(message: Message, x_client_id: Annotated[int, Header()]) -> StreamingResponse:
    """Envoie un message à Wakil ; la réponse arrive en flux SSE, case par case.

    Provisoire : le client est lu dans l'en-tête X-Client-Id. Le morceau 6 le remplacera par un jeton signé.
    """

    def flux():
        etapes = wakil.stream(
            nouveau_tour(message.texte, x_client_id),
            config(x_client_id, message.conversation_id),
            stream_mode="updates",
        )
        for etape in etapes:
            for noeud, ajout in etape.items():
                if ajout.get("reponse"):
                    yield evenement("reponse", {"texte": ajout["reponse"]})
                else:
                    # Seulement le nom de la case et de l'outil : les données de la banque ne partent que dans la réponse.
                    yield evenement("etape", {"noeud": noeud, "outil": ajout.get("outil")})
        yield evenement("fin", {})

    return StreamingResponse(flux(), media_type="text/event-stream")
