"""API de l'agent Wakil.

Une seule route : /chat. La session (cookie) et les pages de l'espace sont servies par portail-api ; agent-api ne parle
jamais à bank-api, il passe par le serveur MCP (apps/mcp-tools).

Lancer (depuis apps/agent-api, serveur MCP et Ollama démarrés) : uv run --env-file ../../.env fastapi dev --port 8001
"""

import asyncio
import json
import logging
import queue
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import agent, reponses
from app.agent import carte_en_attente, config, prochaine_entree
from app.memoire import base_configuree, memoire_postgres
from app.session import ClientConnecte

journal = logging.getLogger(__name__)


@asynccontextmanager
async def cycle_de_vie(app: FastAPI):
    """Au démarrage (≈ @PostConstruct) : l'agent demande au serveur MCP la liste de ses outils, et si la base de
    l'agent est configurée, les conversations vont dans PostgreSQL. À l'arrêt (≈ @PreDestroy), le « with » ferme
    proprement les connexions."""
    try:
        # tools/list maintenant plutôt qu'au premier message : le premier visiteur n'attend pas (le SDK MCP lance sa
        # propre boucle, d'où le fil à part)
        await asyncio.to_thread(agent.le_llm)
    except Exception:
        journal.warning("Serveur MCP injoignable au démarrage : la liste des outils sera demandée au premier message")
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


class Message(BaseModel):
    conversation_id: str = Field(pattern=r"^[A-Za-z0-9-]{1,64}$")  # choisi par le navigateur (un UUID)
    texte: str = Field(min_length=1, max_length=500)  # limite la taille de ce qu'on envoie au LLM
    # Bouton « Payer avec Wakil » sur une facture : paiement de cette facture, sans faire deviner l'intention au LLM.
    facture_id: int | None = None
    # Bouton « Oui » ou « Non » d'une carte : l'identifiant de la carte à laquelle le client répond.
    carte: str | None = Field(default=None, pattern=r"^[A-Za-z0-9-]{1,64}$")


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
            if message.carte is not None and message.carte != carte_en_attente(wakil, conf):
                # Un « Oui » sur une ancienne carte ne doit jamais confirmer l'opération plus récente qui attend.
                file.put(("expiree", None))
            else:
                entree = prochaine_entree(wakil, message.texte, client_id, conf, message.facture_id)
                for etape in wakil.stream(entree, conf, stream_mode="updates"):
                    file.put(("etape", etape))
        except Exception as panne:
            file.put(("panne", panne))
        file.put(("fin", None))

    def flux():
        file: queue.Queue = queue.Queue()
        threading.Thread(target=travailler, args=(file,), daemon=True).start()
        # Ce que les cases ont décidé pendant ce tour : l'outil choisi, le résultat de la banque, une panne éventuelle,
        # et ce qu'est devenue une opération (faite, annulée…).
        outil, donnees, erreur, issue = None, None, False, None
        while True:
            try:
                genre, contenu = file.get(timeout=BATTEMENT)
            except queue.Empty:
                yield ": battement\n\n"  # commentaire SSE : ignoré par le navigateur, garde la connexion ouverte
                continue
            if genre == "fin":
                break
            if genre == "expiree":
                yield evenement(
                    "reponse",
                    {
                        "texte": reponses.CARTE_EXPIREE,
                        "outil": None,
                        "donnees": None,
                        "erreur": False,
                        "issue": "expiree",
                    },
                )
                continue
            if genre == "panne":
                # Le flux a déjà commencé (statut 200 envoyé) : on ne peut plus répondre 500, on prévient par un événement.
                journal.error("Le tour de Wakil a échoué (client %s)", client_id, exc_info=contenu)
                yield evenement("erreur", {"texte": reponses.PANNE})
                continue
            for noeud, ajout in contenu.items():
                if noeud == "__interrupt__":
                    # Le graphe s'est arrêté avant de toucher à l'argent : la carte « Wach nconfirmi ? » part au front.
                    # Son identifiant accompagne la carte : le bouton « Oui » le renverra (voir Message.carte).
                    yield evenement("confirmation", {**ajout[0].value, "carte": ajout[0].id})
                    continue
                outil = ajout.get("outil", outil)
                donnees = ajout.get("resultat", donnees)
                erreur = ajout.get("erreur", erreur)
                issue = ajout.get("issue", issue)
                if ajout.get("reponse"):
                    # Le texte reste la référence ; outil et données servent au front à afficher le solde en
                    # grand ou les opérations en tableau. Ce sont les données du client connecté, et de lui seul.
                    yield evenement(
                        "reponse",
                        {
                            "texte": ajout["reponse"],
                            "outil": outil,
                            "donnees": donnees,
                            "erreur": erreur,
                            "issue": issue,
                        },
                    )
                else:
                    # Seulement le nom de la case et de l'outil : les données de la banque ne partent que dans la réponse.
                    yield evenement("etape", {"noeud": noeud, "outil": ajout.get("outil")})
        yield evenement("fin", {})

    return StreamingResponse(flux(), media_type="text/event-stream")
