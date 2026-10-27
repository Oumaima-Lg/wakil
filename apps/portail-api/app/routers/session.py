"""Ouvrir et fermer la session d'un client de démo. Équivalent Spring : un @RestController."""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app import banque
from app.session import CLIENTS_DEMO, COOKIE, COOKIE_SECURISE, DUREE, ClientConnecte, creer_jeton

router = APIRouter(tags=["session"])


class DemandeSession(BaseModel):
    client_id: int


@router.post("/session")
def ouvrir_session(demande: DemandeSession, response: Response) -> dict:
    """Connexion à un client de démo : pose un cookie qui contient le jeton signé."""
    if demande.client_id not in CLIENTS_DEMO:
        raise HTTPException(status_code=404, detail="Client de démo inconnu")
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


@router.delete("/session", status_code=204)
def fermer_session(response: Response) -> None:
    """Déconnexion : efface le cookie."""
    response.delete_cookie(COOKIE)


@router.get("/moi")
def moi(client_id: ClientConnecte) -> dict:
    """Le profil du client connecté (celui du jeton de session)."""
    return banque.profil(client_id)
