"""Portail de la Banque Atlas Démo : la session du client et les pages de l'espace bancaire. Aucune IA ici.

Le navigateur ne parle jamais à bank-api : il passe par ce « backend for frontend » (le chat, lui, va à agent-api).
Plus tard, le bac à sable des visiteurs (créer et modifier son propre client fictif) viendra ici aussi.

Lancer (depuis apps/portail-api, bank-api démarrée) : uv run --env-file ../../.env fastapi dev --port 8003
Documentation interactive (Swagger) : http://127.0.0.1:8003/docs
"""

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import banque
from app.routers import cartes, espace, session

app = FastAPI(
    title="Banque Atlas Démo · portail",
    description="Session et pages de l'espace bancaire. **Données 100 % fictives – projet de démonstration.**",
)
app.include_router(session.router)
app.include_router(espace.router)
app.include_router(cartes.router)


@app.exception_handler(httpx.HTTPError)
def banque_injoignable(request: Request, erreur: httpx.HTTPError) -> JSONResponse:
    """Si bank-api ne répond pas, le front reçoit un 503 clair au lieu d'une erreur 500, pour toutes les routes.
    Équivalent Spring : un @ExceptionHandler dans un @ControllerAdvice."""
    return JSONResponse(status_code=503, content={"detail": "Banque indisponible"})


@app.exception_handler(banque.RefusBanque)
def refus_de_la_banque(request: Request, refus: banque.RefusBanque) -> JSONResponse:
    """Un refus de la banque (carte déjà active, en opposition…) arrive au front tel quel, avec son code."""
    return JSONResponse(status_code=refus.statut, content={"detail": refus.detail})
