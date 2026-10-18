from fastapi import APIRouter, HTTPException

from app.db import Connexion
from app.schemas import Compte
from app.securite import ClientConnecte

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/{id_client}/comptes")
def lister_comptes(id_client: int, client_id: ClientConnecte, conn: Connexion) -> list[Compte]:
    """Comptes du client connecté, avec un RIB masqué."""
    if id_client != client_id:
        raise HTTPException(status_code=404, detail="Client introuvable")
    lignes = conn.execute("SELECT id, rib FROM comptes WHERE client_id = %s ORDER BY id", (client_id,)).fetchall()
    return [Compte(id=ligne["id"], rib_masque=f"•••• {ligne['rib'][-4:]}") for ligne in lignes]
