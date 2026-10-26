"""API de l'agent Wakil.

Lancer (depuis apps/agent-api, bank-api et Ollama démarrés) : uv run --env-file ../../.env fastapi dev --port 8001
"""

import json
import logging
import queue
import threading
from contextlib import asynccontextmanager, contextmanager
from decimal import Decimal

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import agent, banque, reponses
from app.agent import config, prochaine_entree
from app.memoire import base_configuree, memoire_postgres
from app.session import CLIENTS_DEMO, COOKIE, COOKIE_SECURISE, DUREE, ClientConnecte, creer_jeton

journal = logging.getLogger(__name__)


@asynccontextmanager
async def cycle_de_vie(app: FastAPI):
    """Au démarrage (≈ @PostConstruct) : si la base de l'agent est configurée, les conversations vont dans PostgreSQL.
    À l'arrêt (≈ @PreDestroy), le « with » ferme proprement les connexions."""
    if base_configuree():
        with memoire_postgres() as memoire:
            app.state.wakil = agent.construire(memoire)
            yield
    else:
        yield


app = FastAPI(
    title="Wakil · agent",
    description="Agent bancaire en darija. **Données 100 % fictives – projet de démonstration.**",
    lifespan=cycle_de_vie,
)
# Par défaut, conversations en mémoire vive (tests, ou base de l'agent non configurée).
app.state.wakil = agent.wakil


class DemandeSession(BaseModel):
    client_id: int


class Message(BaseModel):
    conversation_id: str = Field(pattern=r"^[A-Za-z0-9-]{1,64}$")  # choisi par le navigateur (un UUID)
    texte: str = Field(min_length=1, max_length=500)  # limite la taille de ce qu'on envoie au LLM


@contextmanager
def banque_joignable():
    """Si bank-api ne répond pas, le front reçoit un 503 clair au lieu d'une erreur 500."""
    try:
        yield
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Banque indisponible") from None


def resume_client(client_id: int, scenario: str) -> dict:
    compte = banque.compte(client_id)
    factures = banque.factures_impayees(client_id)
    return {
        **banque.profil(client_id),
        "scenario": scenario,
        "solde": compte["solde"],
        "plafond_virement": compte["plafond_virement"],
        "factures_a_payer": len(factures),
        "total_a_payer": str(sum((Decimal(f["montant"]) for f in factures), Decimal("0.00"))),
    }


@app.get("/clients-demo")
def clients_demo() -> list[dict]:
    """Les clients proposés sur l'écran d'accueil, avec un résumé de leur compte lu en direct dans la banque."""
    with banque_joignable():
        return [resume_client(client_id, scenario) for client_id, scenario in CLIENTS_DEMO.items()]


@app.get("/moi")
def moi(client_id: ClientConnecte) -> dict:
    """Le profil du client connecté (celui du jeton de session)."""
    with banque_joignable():
        return banque.profil(client_id)


@app.get("/moi/espace")
def mon_espace(client_id: ClientConnecte) -> dict:
    """Tout ce que l'espace bancaire affiche, en un seul appel (« backend for frontend »). Lecture seule."""
    with banque_joignable():
        return {
            "profil": banque.profil(client_id),
            "compte": banque.compte(client_id),
            "operations": banque.operations(client_id),
            "factures": banque.toutes_factures(client_id),
            "beneficiaires": banque.beneficiaires(client_id),
        }


@app.post("/session")
def ouvrir_session(demande: DemandeSession, response: Response) -> dict:
    """Connexion à un client de démo : pose un cookie qui contient le jeton signé."""
    if demande.client_id not in CLIENTS_DEMO:
        raise HTTPException(status_code=404, detail="Client de démo inconnu")
    with banque_joignable():
        prenom = banque.profil(demande.client_id)["prenom"]
    response.set_cookie(
        COOKIE,
        creer_jeton(demande.client_id),
        max_age=int(DUREE.total_seconds()),
        httponly=True,  # le JavaScript de la page ne peut pas lire le jeton (protection contre le vol par XSS)
        samesite="lax",  # le cookie n'est pas envoyé par un POST venant d'un autre site (protection CSRF)
        secure=COOKIE_SECURISE,
    )
    return {"client_id": demande.client_id, "prenom": prenom}


@app.delete("/session", status_code=204)
def fermer_session(response: Response) -> None:
    """Déconnexion : efface le cookie."""
    response.delete_cookie(COOKIE)


# Pendant que le LLM réfléchit, le flux reste muet. Un proxy coupe une connexion muette trop longtemps (le rewrite de
# Next après 30 s : c'est le cas au premier message, quand Ollama recharge le modèle). On envoie donc un « battement »
# toutes les 10 s.
BATTEMENT = 10  # secondes


def evenement(nom: str, donnees: dict) -> str:
    """Un événement SSE : une ligne « event: », une ligne « data: » en JSON, puis une ligne vide."""
    return f"event: {nom}\ndata: {json.dumps(donnees, ensure_ascii=False)}\n\n"


@app.post("/chat")
def chat(message: Message, client_id: ClientConnecte, request: Request) -> StreamingResponse:
    """Envoie un message à Wakil ; la réponse arrive en flux SSE, case par case.

    Le client vient du jeton signé de la session, jamais du corps de la requête ni du LLM. Si une opération attend
    « Wach nconfirmi ? », le message est la réponse du client ; sinon, c'est une nouvelle demande.
    """
    wakil = request.app.state.wakil

    def travailler(file: queue.Queue) -> None:
        """Fait tourner le graphe dans un fil à part et dépose chaque étape dans la file, puis « fin »."""
        try:
            conf = config(client_id, message.conversation_id)
            etapes = wakil.stream(prochaine_entree(wakil, message.texte, client_id, conf), conf, stream_mode="updates")
            for etape in etapes:
                file.put(("etape", etape))
        except Exception as panne:
            file.put(("panne", panne))
        file.put(("fin", None))

    def flux():
        file: queue.Queue = queue.Queue()
        threading.Thread(target=travailler, args=(file,), daemon=True).start()
        # Ce que les cases ont décidé pendant ce tour : l'outil choisi, le résultat de la banque, une panne éventuelle.
        outil, donnees, erreur = None, None, False
        while True:
            try:
                genre, contenu = file.get(timeout=BATTEMENT)
            except queue.Empty:
                yield ": battement\n\n"  # commentaire SSE : ignoré par le navigateur, garde la connexion ouverte
                continue
            if genre == "fin":
                break
            if genre == "panne":
                # Le flux a déjà commencé (statut 200 envoyé) : on ne peut plus répondre 500, on prévient par un événement.
                journal.error("Le tour de Wakil a échoué (client %s)", client_id, exc_info=contenu)
                yield evenement("erreur", {"texte": reponses.PANNE})
                continue
            for noeud, ajout in contenu.items():
                if noeud == "__interrupt__":
                    # Le graphe s'est arrêté avant de toucher à l'argent : la carte « Wach nconfirmi ? » part au front.
                    yield evenement("confirmation", ajout[0].value)
                    continue
                outil = ajout.get("outil", outil)
                donnees = ajout.get("resultat", donnees)
                erreur = ajout.get("erreur", erreur)
                if ajout.get("reponse"):
                    # Le texte reste la référence ; outil et données servent au front à afficher le solde en
                    # grand ou les opérations en tableau. Ce sont les données du client connecté, et de lui seul.
                    yield evenement(
                        "reponse", {"texte": ajout["reponse"], "outil": outil, "donnees": donnees, "erreur": erreur}
                    )
                else:
                    # Seulement le nom de la case et de l'outil : les données de la banque ne partent que dans la réponse.
                    yield evenement("etape", {"noeud": noeud, "outil": ajout.get("outil")})
        yield evenement("fin", {})

    return StreamingResponse(flux(), media_type="text/event-stream")
