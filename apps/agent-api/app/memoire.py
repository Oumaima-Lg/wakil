"""Où Wakil range ses conversations : dans PostgreSQL, base séparée de l'agent (voir base-agent.sh).

Avec InMemorySaver, tout vivait en mémoire vive : un redémarrage d'agent-api effaçait les conversations, et
surtout les paiements qui attendaient « Wach nconfirmi ? ». Avec PostgresSaver, l'état est écrit après chaque
case du graphe : la conversation reprend là où elle s'était arrêtée.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def base_configuree() -> bool:
    return "AGENT_POSTGRES_USER" in os.environ


@contextmanager
def memoire_postgres() -> Iterator[PostgresSaver]:
    """Ouvre un pool de connexions vers la base de l'agent et crée les tables du checkpointer si besoin."""
    conninfo = make_conninfo(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        user=os.environ["AGENT_POSTGRES_USER"],
        password=os.environ["AGENT_POSTGRES_PASSWORD"],
        dbname=os.environ["AGENT_POSTGRES_DB"],
    )
    with ConnectionPool(
        conninfo,
        # Réglages demandés par PostgresSaver : chaque écriture validée tout de suite, pas de requêtes préparées
        # (incompatibles avec certains pools), lignes en dict.
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        check=ConnectionPool.check_connection,  # comme bank-api : survit à un redémarrage de PostgreSQL
    ) as pool:
        memoire = PostgresSaver(pool)
        memoire.setup()  # crée ses tables la première fois (comme une migration)
        yield memoire
