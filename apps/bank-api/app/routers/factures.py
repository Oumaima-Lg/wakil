from fastapi import APIRouter, HTTPException
from psycopg.types.json import Jsonb

from app.db import Connexion
from app.schemas import Facture, Paiement
from app.securite import ClientConnecte

router = APIRouter(tags=["Factures"])


@router.get("/clients/{id_client}/factures")
def lister_factures(id_client: int, client_id: ClientConnecte, conn: Connexion) -> list[Facture]:
    """Factures du client connecté (payées et impayées)."""
    if id_client != client_id:
        raise HTTPException(status_code=404, detail="Client introuvable")
    lignes = conn.execute(
        "SELECT id, fournisseur, montant, statut FROM factures WHERE client_id = %s ORDER BY id",
        (client_id,),
    ).fetchall()
    return [Facture(**ligne) for ligne in lignes]


@router.post("/factures/{facture_id}/payer")
def payer_facture(facture_id: int, client_id: ClientConnecte, conn: Connexion) -> Paiement:
    """Paye une facture avec le compte du client connecté.

    Règles : la facture appartient au client, elle est impayée, le solde est suffisant.
    Effets, tous ensemble ou aucun : débit du compte, transaction, statut « payee », ligne d'audit.
    """
    # Comme @Transactional : tout le bloc est validé ensemble (COMMIT), ou tout est annulé (ROLLBACK).
    with conn.transaction():
        # FOR UPDATE verrouille la facture jusqu'à la fin du bloc : si deux demandes de paiement
        # arrivent en même temps, la seconde attend, puis voit « payee » et est refusée.
        facture = conn.execute(
            "SELECT id, fournisseur, montant, statut FROM factures"
            " WHERE id = %s AND client_id = %s FOR UPDATE",
            (facture_id, client_id),
        ).fetchone()
        if facture is None:
            raise HTTPException(status_code=404, detail="Facture introuvable")
        if facture["statut"] == "payee":
            raise HTTPException(status_code=409, detail="Facture déjà payée")

        # Dans la Banque Atlas Démo, chaque client a un seul compte.
        compte = conn.execute(
            "SELECT id, solde FROM comptes WHERE client_id = %s ORDER BY id LIMIT 1 FOR UPDATE",
            (client_id,),
        ).fetchone()
        if compte["solde"] < facture["montant"]:
            raise HTTPException(status_code=409, detail="Solde insuffisant")

        nouveau_solde = conn.execute(
            "UPDATE comptes SET solde = solde - %s WHERE id = %s RETURNING solde",
            (facture["montant"], compte["id"]),
        ).fetchone()["solde"]
        conn.execute("UPDATE factures SET statut = 'payee' WHERE id = %s", (facture_id,))
        conn.execute(
            "INSERT INTO transactions (compte_id, montant, libelle) VALUES (%s, %s, %s)",
            (compte["id"], -facture["montant"], f"Paiement facture {facture['fournisseur']}"),
        )
        conn.execute(
            "INSERT INTO audit (client_id, action, details) VALUES (%s, 'paiement_facture', %s)",
            (client_id, Jsonb({"facture_id": facture_id, "compte_id": compte["id"], "montant": str(facture["montant"])})),
        )

    return Paiement(
        facture_id=facture_id,
        fournisseur=facture["fournisseur"],
        montant=facture["montant"],
        nouveau_solde=nouveau_solde,
    )
