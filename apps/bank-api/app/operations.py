"""Outils communs aux opérations qui déplacent de l'argent (paiement de facture, virement)."""

from decimal import Decimal
from typing import Annotated

from fastapi import HTTPException, Query

# Vérification à blanc : la route fait toute l'opération dans sa transaction (règles, débit, audit), puis l'annule
# au lieu de la valider. Les règles vérifiées sont donc exactement celles du vrai paiement, et le « solde après »
# vient de la vraie requête SQL. (Même idée que le dryRun de Kubernetes.)
Simulation = Annotated[
    bool,
    Query(description="Vérification à blanc : tout est vérifié et calculé, puis annulé. Rien ne change sur le compte."),
]


def refus(code: str, message: str, **montants: Decimal) -> HTTPException:
    """Refus d'une règle métier (409), avec un code lisible par un programme et les montants utiles.

    Exemple : {"code": "solde_insuffisant", "message": "Solde insuffisant", "solde": "150.00", "montant": "349.00"}.
    L'agent s'en sert pour expliquer le refus en darija avec les bons chiffres, sans les recalculer.
    """
    details = {nom: f"{valeur:.2f}" for nom, valeur in montants.items()}  # montants en texte exact, comme ailleurs
    return HTTPException(status_code=409, detail={"code": code, "message": message, **details})
