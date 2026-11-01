from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.db import Connexion
from app.schemas import Beneficiaire, Client, Compte, EntreeAudit, masquer_rib
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


def libelle_audit(ligne: dict) -> str:
    """La phrase que lit le client, d'après le code de l'action et ses détails."""
    details, action = ligne["details"], ligne["action"]
    carte = details.get("numero_masque", "")
    match action:
        case "paiement_facture":
            return f"Paiement de la facture {ligne['fournisseur'] or ''}".strip()
        case "virement":
            return f"Virement vers {ligne['beneficiaire']}" if ligne["beneficiaire"] else "Virement"
        case "carte_bloquee":
            return f"Carte {carte} bloquée"
        case "carte_debloquee":
            return f"Carte {carte} débloquée"
        case "carte_opposition":
            return f"Carte {carte} mise en opposition ({details.get('motif', '')})"
        case "carte_remplacee":
            return f"Nouvelle carte {details.get('nouvelle', '')} commandée (remplace {carte})"
    return action


@router.get("/{id_client}/audit")
def journal_audit(
    id_client: int, client_id: ClientConnecte, conn: Connexion, limite: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[EntreeAudit]:
    """Le journal des opérations sensibles du client connecté (paiements, virements, cartes), la plus récente
    d'abord : ce que Wakil a fait pour lui. Sans les identifiants internes de la banque."""
    verifier_client(id_client, client_id)
    lignes = conn.execute(
        "SELECT a.confirmee_le AS date, a.action, a.details, f.fournisseur, b.nom AS beneficiaire FROM audit a"
        " LEFT JOIN factures f ON a.action = 'paiement_facture' AND f.id = (a.details->>'facture_id')::int"
        " LEFT JOIN beneficiaires b ON a.action = 'virement' AND b.id = (a.details->>'beneficiaire_id')::int"
        " WHERE a.client_id = %s ORDER BY a.confirmee_le DESC, a.id DESC LIMIT %s",
        (client_id, limite),
    ).fetchall()
    return [
        EntreeAudit(
            date=ligne["date"],
            action=ligne["action"],
            libelle=libelle_audit(ligne),
            montant=Decimal(ligne["details"]["montant"]) if "montant" in ligne["details"] else None,
        )
        for ligne in lignes
    ]
