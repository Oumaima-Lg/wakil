"""Route des virements."""

import psycopg
from fastapi import APIRouter, HTTPException
from psycopg.types.json import Jsonb

from app.db import Connexion
from app.operations import Simulation, refus
from app.schemas import DemandeVirement, Virement, masquer_rib
from app.securite import ClientConnecte

router = APIRouter(tags=["Virements"])


@router.post("/virements")
def faire_virement(
    demande: DemandeVirement, client_id: ClientConnecte, conn: Connexion, simulation: Simulation = False
) -> Virement:
    """Vire de l'argent du compte du client connecté vers un de ses bénéficiaires.

    Règles : le bénéficiaire est connu du client, le montant est positif,
    il ne dépasse ni le plafond de virement ni le solde.
    Effets, tous ensemble ou aucun : débit, crédit du compte du bénéficiaire, transactions, ligne d'audit.
    Avec ?simulation=true : tout est vérifié et calculé, puis annulé (vérification à blanc avant la confirmation).
    """
    with conn.transaction():
        beneficiaire = conn.execute(
            "SELECT nom, rib FROM beneficiaires WHERE id = %s AND client_id = %s",
            (demande.beneficiaire_id, client_id),
        ).fetchone()
        if beneficiaire is None:
            raise HTTPException(status_code=404, detail="Bénéficiaire inconnu")

        # Compte du client (un seul par client) et compte du bénéficiaire s'il est client de la banque.
        source_id = conn.execute(
            "SELECT id FROM comptes WHERE client_id = %s ORDER BY id LIMIT 1", (client_id,)
        ).fetchone()["id"]
        destination = conn.execute("SELECT id FROM comptes WHERE rib = %s", (beneficiaire["rib"],)).fetchone()
        destination_id = destination["id"] if destination else None
        if destination_id == source_id:
            raise refus("virement_vers_soi", "Virement vers son propre compte impossible")

        # Verrouille les comptes toujours dans le même ordre (par id) : deux virements croisés,
        # A vers B et B vers A, ne peuvent pas s'attendre l'un l'autre indéfiniment (interblocage).
        ids = [i for i in (source_id, destination_id) if i is not None]
        comptes = {
            ligne["id"]: ligne
            for ligne in conn.execute(
                "SELECT id, solde, plafond_virement FROM comptes WHERE id = ANY(%s) ORDER BY id FOR UPDATE",
                (ids,),
            ).fetchall()
        }
        source = comptes[source_id]
        if demande.montant > source["plafond_virement"]:
            raise refus(
                "plafond_depasse",
                "Plafond de virement dépassé",
                plafond=source["plafond_virement"],
                montant=demande.montant,
            )
        if demande.montant > source["solde"]:
            raise refus("solde_insuffisant", "Solde insuffisant", solde=source["solde"], montant=demande.montant)

        nouveau_solde = conn.execute(
            "UPDATE comptes SET solde = solde - %s WHERE id = %s RETURNING solde",
            (demande.montant, source_id),
        ).fetchone()["solde"]
        conn.execute(
            "INSERT INTO transactions (compte_id, montant, libelle) VALUES (%s, %s, %s)",
            (source_id, -demande.montant, f"Virement vers {beneficiaire['nom']}"),
        )
        if destination_id is not None:
            emetteur = conn.execute(
                "SELECT prenom || ' ' || nom AS nom FROM clients WHERE id = %s", (client_id,)
            ).fetchone()["nom"]
            conn.execute("UPDATE comptes SET solde = solde + %s WHERE id = %s", (demande.montant, destination_id))
            conn.execute(
                "INSERT INTO transactions (compte_id, montant, libelle) VALUES (%s, %s, %s)",
                (destination_id, demande.montant, f"Virement reçu de {emetteur}"),
            )
        conn.execute(
            "INSERT INTO audit (client_id, action, details) VALUES (%s, 'virement', %s)",
            (
                client_id,
                Jsonb(
                    {
                        "beneficiaire_id": demande.beneficiaire_id,
                        "compte_source": source_id,
                        "compte_destination": destination_id,
                        "montant": str(demande.montant),
                    }
                ),
            ),
        )
        if simulation:
            raise psycopg.Rollback()  # vérification à blanc : tout le bloc est annulé (voir factures.py)

    return Virement(
        beneficiaire=beneficiaire["nom"],
        beneficiaire_rib_masque=masquer_rib(beneficiaire["rib"]),
        montant=demande.montant,
        nouveau_solde=nouveau_solde,
        simulation=simulation,
    )
