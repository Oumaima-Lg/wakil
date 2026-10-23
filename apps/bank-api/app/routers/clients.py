from fastapi import APIRouter, HTTPException

from app.db import Connexion
from app.schemas import Client, Compte
from app.securite import ClientConnecte

router = APIRouter(prefix="/clients", tags=["Clients"])


def verifier_client(id_client: int, client_id: int) -> None:
    """L'id de l'URL doit être celui du client connecté. 404 et pas 403 : on ne révèle pas qui existe."""
    if id_client != client_id:
        raise HTTPException(status_code=404, detail="Client introuvable")


@router.get("/{id_client}")
def profil(id_client: int, client_id: ClientConnecte, conn: Connexion) -> Client:
    """Profil du client connecté."""
    verifier_client(id_client, client_id)
    ligne = conn.execute("SELECT id, civilite, prenom, nom, ville FROM clients WHERE id = %s", (client_id,)).fetchone()
    if ligne is None:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return Client(**ligne)


@router.get("/{id_client}/comptes")
def lister_comptes(id_client: int, client_id: ClientConnecte, conn: Connexion) -> list[Compte]:
    """Comptes du client connecté, avec un RIB masqué."""
    verifier_client(id_client, client_id)
    lignes = conn.execute(
        "SELECT id, rib, plafond_virement FROM comptes WHERE client_id = %s ORDER BY id", (client_id,)
    ).fetchall()
    return [
        Compte(id=ligne["id"], rib_masque=f"•••• {ligne['rib'][-4:]}", plafond_virement=ligne["plafond_virement"])
        for ligne in lignes
    ]
