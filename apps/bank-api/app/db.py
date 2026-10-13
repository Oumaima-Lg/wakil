import os
from typing import Annotated

import psycopg
from fastapi import Depends
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    make_conninfo(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    ),
    kwargs={"row_factory": dict_row},  # chaque ligne devient un dict : ligne["solde"]
    open=False,  # ouvert au démarrage de l'application (voir main.py)
)


def get_conn():
    """Prête une connexion pour la durée d'une requête HTTP.

    Comme @Transactional : COMMIT si la route se termine normalement, ROLLBACK si elle lève une erreur.
    """
    with pool.connection() as conn:
        yield conn


# Raccourci à mettre dans la signature d'une route pour recevoir une connexion.
Connexion = Annotated[psycopg.Connection, Depends(get_conn)]
