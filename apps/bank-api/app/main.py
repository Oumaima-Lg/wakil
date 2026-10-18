"""Point d'entrée de l'API. Équivalent Spring : la classe annotée @SpringBootApplication.

Lancer (depuis apps/bank-api) : uv run --env-file ../../.env fastapi dev
Documentation interactive (Swagger) : http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import pool
from app.routers import clients, comptes, factures, virements


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ouvre le pool de connexions au démarrage et le ferme à l'arrêt."""
    pool.open()
    yield
    pool.close()


app = FastAPI(
    title="Banque Atlas Démo",
    description="API de la banque fictive de Wakil. **Données 100 % fictives – projet de démonstration.**",
    lifespan=lifespan,
)
app.include_router(clients.router)
app.include_router(comptes.router)
app.include_router(factures.router)
app.include_router(virements.router)
