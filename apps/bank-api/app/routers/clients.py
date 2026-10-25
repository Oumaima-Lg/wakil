from fastapi import APIRouter, HTTPException

from app.db import Connexion
from app.schemas import Beneficiaire, Client, Compte, masquer_rib
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
        Compte(id=ligne["id"], rib_masque=masquer_rib(ligne["rib"]), plafond_virement=ligne["plafond_virement"])
        for ligne in lignes
    ]


@router.get("/{id_client}/beneficiaires")
def lister_beneficiaires(id_client: int, client_id: ClientConnecte, conn: Connexion) -> list[Beneficiaire]:
    """Bénéficiaires du client connecté. On dit seulement s'ils sont clients de la banque, rien d'autre sur eux."""
    verifier_client(id_client, client_id)
    lignes = conn.execute(
        "SELECT b.id, b.nom, b.rib, EXISTS (SELECT 1 FROM comptes c WHERE c.rib = b.rib) AS interne"
        " FROM beneficiaires b WHERE b.client_id = %s ORDER BY b.nom",
        (client_id,),
    ).fetchall()
    return [
        Beneficiaire(id=ligne["id"], nom=ligne["nom"], rib_masque=masquer_rib(ligne["rib"]), interne=ligne["interne"])
        for ligne in lignes
    ]
