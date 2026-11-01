"""Idempotence des opérations qui déplacent de l'argent : même clé et même demande, même réponse, une seule exécution.

Le client de l'API envoie un en-tête Idempotency-Key, unique pour chaque opération (le serveur MCP de Wakil y met
l'identifiant de la carte « Wach nconfirmi ? »). La banque garde la clé et sa réponse 24 h, dans la même transaction
que l'opération :
- même clé, même demande : la réponse déjà donnée est renvoyée, rien n'est refait ;
- même clé, autre demande (autre montant, autre facture) : refus 409 « cle_reutilisee » ;
- refus métier ou erreur : la transaction est annulée, clé comprise. Rien n'ayant bougé, la demande pourra être refaite.

Si deux demandes avec la même clé arrivent en même temps, la seconde attend la fin de la première (index unique), puis
reçoit sa réponse : jamais deux exécutions. Équivalent Spring : une table de clés consultée dans le même @Transactional.
"""

import hashlib
import json
from typing import Annotated

from fastapi import Header
from psycopg import Connection
from psycopg.types.json import Jsonb

from app.operations import refus

CleIdempotence = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        pattern=r"^[A-Za-z0-9_-]{1,100}$",
        description="Clé unique par opération : la rejouer renvoie la même réponse, sans refaire l'opération.",
    ),
]
DUREE = "24 hours"  # durée de vie d'une clé (intervalle PostgreSQL)


def empreinte(route: str, corps: dict) -> str:
    """Ce qui identifie la demande : la route et son contenu. Une clé réutilisée pour autre chose se voit ainsi."""
    return hashlib.sha256(json.dumps([route, corps], sort_keys=True, default=str).encode()).hexdigest()


def deja_faite(conn: Connection, client_id: int, cle: str, route: str, corps: dict) -> dict | None:
    """À appeler au début de la transaction de l'opération : réserve la clé (première fois, renvoie None), ou renvoie
    la réponse déjà donnée pour cette clé."""
    conn.execute(
        f"DELETE FROM idempotence WHERE client_id = %s AND cle = %s AND cree_le < now() - interval '{DUREE}'",
        (client_id, cle),
    )
    signature = empreinte(route, corps)
    reservee = conn.execute(
        "INSERT INTO idempotence (client_id, cle, empreinte) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING RETURNING cle",
        (client_id, cle, signature),
    ).fetchone()
    if reservee is not None:
        return None
    ligne = conn.execute(
        "SELECT empreinte, reponse FROM idempotence WHERE client_id = %s AND cle = %s", (client_id, cle)
    ).fetchone()
    if ligne["empreinte"] != signature:
        raise refus("cle_reutilisee", "Cette clé d'idempotence a déjà servi pour une autre demande")
    return ligne["reponse"]


def retenir(conn: Connection, client_id: int, cle: str, reponse: dict) -> None:
    """Garde la réponse de l'opération avec sa clé, dans la même transaction."""
    conn.execute(
        "UPDATE idempotence SET reponse = %s WHERE client_id = %s AND cle = %s", (Jsonb(reponse), client_id, cle)
    )
