"""Préparation commune : un vrai serveur MCP en HTTP (l'en-tête X-Client-Id n'existe qu'en HTTP), et une fausse banque.

Les tests parlent au serveur comme agent-api : client MCP officiel, transport Streamable HTTP.
"""

import asyncio
import socket
import threading
import time
from decimal import Decimal

import pytest
import uvicorn
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from app import banque
from app.serveur import CONFIRMATION, app

EAU, INTERNET = "Eau & Électricité (démo)", "Internet (démo)"
FACTURES = {
    1: [{"id": 1, "fournisseur": EAU, "montant": "312.00", "statut": "impayee"},
        {"id": 2, "fournisseur": INTERNET, "montant": "249.00", "statut": "impayee"}],
    2: [{"id": 7, "fournisseur": INTERNET, "montant": "349.00", "statut": "impayee"}],
}  # fmt: skip
BENEFICIAIRES = {
    1: [{"id": 1, "nom": "Fatima Lahlou", "rib_masque": "•••• 8633", "interne": True},
        {"id": 2, "nom": "Omar Benali", "rib_masque": "•••• 1120", "interne": False}],
    3: [{"id": 5, "nom": "Fatima Lahlou", "rib_masque": "•••• 8633", "interne": True},
        {"id": 6, "nom": "Fatima Zahra Idrissi", "rib_masque": "•••• 4410", "interne": True}],
}  # fmt: skip
PLAFONDS = {1: Decimal("10000.00"), 2: Decimal("5000.00"), 3: Decimal("2000.00")}


class FausseBanque:
    """Doublure de bank-api, avec ses vraies règles (solde, plafond) et ses refus 409. Note chaque appel."""

    def __init__(self):
        self.soldes = {1: Decimal("2350.00"), 2: Decimal("150.00"), 3: Decimal("18500.00")}
        self.appels = []

    def solde(self, client_id):
        self.appels.append(("solde", client_id))
        return {"compte_id": client_id, "solde": f"{self.soldes[client_id]:.2f}", "devise": "DH"}

    def compte(self, client_id):
        return {"id": client_id, "rib_masque": "•••• 9114", "plafond_virement": f"{PLAFONDS[client_id]:.2f}"}

    def transactions(self, client_id):
        return [{"id": 11, "date": "2026-10-21T09:25:00Z", "montant": "-57.98", "libelle": "Café"}]

    def factures_impayees(self, client_id):
        return FACTURES.get(client_id, [])

    def beneficiaires(self, client_id):
        return BENEFICIAIRES.get(client_id, [])

    def depenses(self, client_id, du, au):
        self.appels.append(("depenses", client_id, du, au))
        return {"du": du.isoformat(), "au": au.isoformat(), "depenses": "512.50", "entrees": "6000.00", "nombre": 4,
                "par_categorie": [{"categorie": "factures", "nom": "Factures", "total": "312.00", "nombre": 1},
                                  {"categorie": "restaurant", "nom": "Restaurant", "total": "200.50", "nombre": 2}],
                "plus_grosse": {"id": 3, "date": "2026-10-15T09:00:00Z", "montant": "-312.00",
                                "libelle": "Paiement facture Eau & Électricité (démo)"}}  # fmt: skip

    def _verifier_solde(self, client_id, montant):
        if montant > self.soldes[client_id]:
            raise banque.RefusBanque(
                {"code": "solde_insuffisant", "message": "Solde insuffisant",
                 "solde": f"{self.soldes[client_id]:.2f}", "montant": f"{montant:.2f}"}
            )  # fmt: skip

    def payer(self, client_id, facture_id, simulation):
        facture = next(f for f in FACTURES[client_id] if f["id"] == facture_id)
        montant = Decimal(facture["montant"])
        self.appels.append(("paiement", client_id, facture_id, simulation))
        self._verifier_solde(client_id, montant)
        nouveau = self.soldes[client_id] - montant
        if not simulation:
            self.soldes[client_id] = nouveau
        return {"facture_id": facture_id, "fournisseur": facture["fournisseur"], "montant": facture["montant"],
                "nouveau_solde": f"{nouveau:.2f}", "simulation": simulation}  # fmt: skip

    def virer(self, client_id, beneficiaire_id, montant, simulation):
        beneficiaire = next(b for b in BENEFICIAIRES[client_id] if b["id"] == beneficiaire_id)
        self.appels.append(("virement", client_id, beneficiaire_id, montant, simulation))
        if montant > PLAFONDS[client_id]:
            raise banque.RefusBanque(
                {"code": "plafond_depasse", "message": "Plafond de virement dépassé",
                 "plafond": f"{PLAFONDS[client_id]:.2f}", "montant": f"{montant:.2f}"}
            )  # fmt: skip
        self._verifier_solde(client_id, montant)
        nouveau = self.soldes[client_id] - montant
        if not simulation:
            self.soldes[client_id] = nouveau
        return {"beneficiaire": beneficiaire["nom"], "beneficiaire_rib_masque": beneficiaire["rib_masque"],
                "montant": f"{montant:.2f}", "nouveau_solde": f"{nouveau:.2f}", "simulation": simulation}  # fmt: skip


@pytest.fixture(autouse=True)
def fausse_banque(monkeypatch):
    """Le serveur tourne dans ce même processus : remplacer les fonctions de app.banque suffit."""
    fausse = FausseBanque()
    for nom in ("solde", "compte", "transactions", "factures_impayees", "beneficiaires", "depenses", "payer", "virer"):
        monkeypatch.setattr(banque, nom, getattr(fausse, nom))
    return fausse


@pytest.fixture(scope="session")
def url_du_serveur():
    """Lance le vrai serveur MCP (uvicorn) sur un port libre, le temps des tests."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    serveur = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=serveur.run, daemon=True).start()
    while not serveur.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/mcp"
    serveur.should_exit = True


@pytest.fixture
def mcp(url_du_serveur):
    """Parle au serveur comme agent-api : client MCP officiel, en-tête X-Client-Id, confirmation dans _meta."""

    def client(client_id):
        entetes = {"X-Client-Id": str(client_id)} if client_id is not None else {}
        return Client(streamable_http_client(url_du_serveur, http_client=create_mcp_http_client(headers=entetes)))

    def appeler(nom, arguments=None, client_id=1, confirmation=None):
        async def faire():
            async with client(client_id) as c:
                meta = {CONFIRMATION: confirmation} if confirmation else None
                return await c.call_tool(nom, arguments or {}, meta=meta)

        return asyncio.run(faire())

    def lister():
        async def faire():
            async with client(1) as c:
                return (await c.list_tools()).tools

        return asyncio.run(faire())

    appeler.lister = lister
    return appeler
