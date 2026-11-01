"""Routes des cartes : la liste, puis les changements d'état, toujours dans le même ordre possible.

    active ⇄ bloquee      blocage temporaire (carte égarée, doute) : réversible
    active / bloquee → opposee      perte ou vol : définitif, la carte ne revient jamais
    opposee → nouvelle carte         remplacement, une seule fois : nouveau numéro, l'ancienne reste en opposition

Un changement interdit (débloquer une carte en opposition…) est un refus 409 avec un code, comme pour les paiements.
Chaque changement est écrit dans le journal d'audit. Avec ?simulation=true, tout est vérifié puis annulé : Wakil le
fait avant d'afficher sa carte de confirmation (il pourra seulement bloquer une carte, décision du 31/10/2026).
"""

from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from psycopg.types.json import Jsonb

from app.db import Connexion
from app.operations import Simulation, refus
from app.routers.clients import verifier_client
from app.schemas import Carte, DemandeOpposition
from app.securite import ClientConnecte

router = APIRouter(tags=["Cartes"])
COLONNES = "id, numero_masque, expiration, statut, motif_opposition, remplacee_par"


@router.get("/clients/{id_client}/cartes")
def lister_cartes(id_client: int, client_id: ClientConnecte, conn: Connexion) -> list[Carte]:
    """Cartes du client connecté, avec leur état."""
    verifier_client(id_client, client_id)
    lignes = conn.execute(f"SELECT {COLONNES} FROM cartes WHERE client_id = %s ORDER BY id", (client_id,)).fetchall()
    return [Carte(**ligne) for ligne in lignes]


def carte_du_client(carte_id: int, client_id: ClientConnecte, conn: Connexion) -> int:
    """L'id de la carte, si elle appartient au client connecté. Sinon : 404 (on ne révèle pas qui l'a)."""
    if conn.execute("SELECT 1 FROM cartes WHERE id = %s AND client_id = %s", (carte_id, client_id)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    return carte_id


CarteDuClient = Annotated[int, Depends(carte_du_client)]


def changer_etat(
    conn: psycopg.Connection,
    client_id: int,
    carte_id: int,
    depuis: set[str],
    vers: str,
    action: str,
    simulation: bool,
    motif: str | None = None,
) -> Carte:
    """Fait passer la carte de l'un des états « depuis » à l'état « vers », ou refuse avec le code qui explique."""
    with conn.transaction():
        # FOR UPDATE : deux demandes en même temps sur la même carte passent l'une après l'autre.
        carte = conn.execute(f"SELECT {COLONNES} FROM cartes WHERE id = %s FOR UPDATE", (carte_id,)).fetchone()
        if carte["statut"] not in depuis:
            if carte["statut"] == "opposee":
                raise refus("carte_en_opposition", "Carte en opposition : ce changement est définitivement impossible")
            # Sinon, avec trois états seulement, la carte est déjà dans l'état demandé (bloquer une carte bloquée…).
            raise refus(f"carte_deja_{vers}", "La carte est déjà dans cet état")
        nouvelle = conn.execute(
            f"UPDATE cartes SET statut = %s, motif_opposition = %s, modifiee_le = now() WHERE id = %s RETURNING {COLONNES}",
            (vers, motif, carte_id),
        ).fetchone()
        details = {"carte_id": carte_id, "numero_masque": carte["numero_masque"], **({"motif": motif} if motif else {})}
        conn.execute(
            "INSERT INTO audit (client_id, action, details) VALUES (%s, %s, %s)", (client_id, action, Jsonb(details))
        )
        resultat = Carte(**nouvelle)
        if simulation:
            raise psycopg.Rollback()  # vérification à blanc : tout est annulé (voir factures.py)
    return resultat


@router.post("/cartes/{carte_id}/blocage")
def bloquer_carte(
    carte_id: CarteDuClient, client_id: ClientConnecte, conn: Connexion, simulation: Simulation = False
) -> Carte:
    """Bloque une carte active (temporaire, réversible)."""
    return changer_etat(conn, client_id, carte_id, {"active"}, "bloquee", "carte_bloquee", simulation)


@router.post("/cartes/{carte_id}/deblocage")
def debloquer_carte(
    carte_id: CarteDuClient, client_id: ClientConnecte, conn: Connexion, simulation: Simulation = False
) -> Carte:
    """Débloque une carte bloquée. Une carte en opposition ne se débloque jamais."""
    return changer_etat(conn, client_id, carte_id, {"bloquee"}, "active", "carte_debloquee", simulation)


@router.post("/cartes/{carte_id}/opposition")
def faire_opposition(
    carte_id: CarteDuClient,
    demande: DemandeOpposition,
    client_id: ClientConnecte,
    conn: Connexion,
    simulation: Simulation = False,
) -> Carte:
    """Met une carte en opposition (perte ou vol) : définitif."""
    return changer_etat(
        conn, client_id, carte_id, {"active", "bloquee"}, "opposee", "carte_opposition", simulation, demande.motif
    )


@router.post("/cartes/{carte_id}/remplacement")
def remplacer_carte(carte_id: CarteDuClient, client_id: ClientConnecte, conn: Connexion) -> Carte:
    """Commande une nouvelle carte après une opposition, comme dans une vraie banque : nouveau numéro (fictif) et
    nouvelle date d'expiration (dans 4 ans). Une seule fois par carte en opposition."""
    with conn.transaction():
        ancienne = conn.execute(
            "SELECT id, compte_id, numero_masque, statut, remplacee_par FROM cartes WHERE id = %s FOR UPDATE",
            (carte_id,),
        ).fetchone()
        if ancienne["statut"] != "opposee":
            raise refus("carte_non_opposee", "Une carte se remplace seulement après une opposition")
        if ancienne["remplacee_par"] is not None:
            raise refus("carte_deja_remplacee", "Cette carte a déjà été remplacée")
        # Sans hasard, comme les cartes de démo : le rang de la carte sur le compte change le numéro.
        rang = conn.execute(
            "SELECT count(*) AS n FROM cartes WHERE compte_id = %s", (ancienne["compte_id"],)
        ).fetchone()
        aujourd_hui = datetime.now(ZoneInfo("Africa/Casablanca"))
        nouvelle = conn.execute(
            "INSERT INTO cartes (client_id, compte_id, numero_masque, expiration) VALUES (%s, %s, %s, %s)"
            f" RETURNING {COLONNES}",
            (
                client_id,
                ancienne["compte_id"],
                f"•••• {(client_id * 7919 + rang['n'] * 104729) % 10000:04d}",
                f"{aujourd_hui.month:02d}/{(aujourd_hui.year + 4) % 100:02d}",
            ),
        ).fetchone()
        conn.execute(
            "UPDATE cartes SET remplacee_par = %s, modifiee_le = now() WHERE id = %s", (nouvelle["id"], carte_id)
        )
        details = {
            "carte_id": carte_id,
            "numero_masque": ancienne["numero_masque"],
            "nouvelle": nouvelle["numero_masque"],
        }
        conn.execute(
            "INSERT INTO audit (client_id, action, details) VALUES (%s, 'carte_remplacee', %s)",
            (client_id, Jsonb(details)),
        )
    return Carte(**nouvelle)
