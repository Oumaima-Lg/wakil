"""API de l'agent Wakil.

Lancer (depuis apps/agent-api, bank-api et Ollama démarrés) : uv run --env-file ../../.env fastapi dev --port 8001
"""

import json

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent import config, nouveau_tour, wakil
from app.session import CLIENTS_DEMO, COOKIE, COOKIE_SECURISE, DUREE, ClientConnecte, creer_jeton

app = FastAPI(
    title="Wakil · agent",
    description="Agent bancaire en darija. **Données 100 % fictives – projet de démonstration.**",
)


class DemandeSession(BaseModel):
    client_id: int


class Message(BaseModel):
    conversation_id: str = Field(pattern=r"^[A-Za-z0-9-]{1,64}$")  # choisi par le navigateur (un UUID)
    texte: str = Field(min_length=1, max_length=500)  # limite la taille de ce qu'on envoie au LLM


@app.get("/clients-demo")
def clients_demo() -> list[dict]:
    """Les clients proposés sur l'écran d'accueil."""
    return [{"id": client_id, "prenom": prenom} for client_id, prenom in CLIENTS_DEMO.items()]


@app.post("/session")
def ouvrir_session(demande: DemandeSession, response: Response) -> dict:
    """Connexion à un client de démo : pose un cookie qui contient le jeton signé."""
    if demande.client_id not in CLIENTS_DEMO:
        raise HTTPException(status_code=404, detail="Client de démo inconnu")
    response.set_cookie(
        COOKIE,
        creer_jeton(demande.client_id),
        max_age=int(DUREE.total_seconds()),
        httponly=True,  # le JavaScript de la page ne peut pas lire le jeton (protection contre le vol par XSS)
        samesite="lax",  # le cookie n'est pas envoyé par un POST venant d'un autre site (protection CSRF)
        secure=COOKIE_SECURISE,
    )
    return {"client_id": demande.client_id, "prenom": CLIENTS_DEMO[demande.client_id]}


@app.delete("/session", status_code=204)
def fermer_session(response: Response) -> None:
    """Déconnexion : efface le cookie."""
    response.delete_cookie(COOKIE)


def evenement(nom: str, donnees: dict) -> str:
    """Un événement SSE : une ligne « event: », une ligne « data: » en JSON, puis une ligne vide."""
    return f"event: {nom}\ndata: {json.dumps(donnees, ensure_ascii=False)}\n\n"


@app.post("/chat")
def chat(message: Message, client_id: ClientConnecte) -> StreamingResponse:
    """Envoie un message à Wakil ; la réponse arrive en flux SSE, case par case.

    Le client vient du jeton signé de la session, jamais du corps de la requête ni du LLM.
    """

    def flux():
        etapes = wakil.stream(
            nouveau_tour(message.texte, client_id),
            config(client_id, message.conversation_id),
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
