from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class Solde(BaseModel):
    compte_id: int
    solde: Decimal  # Decimal, jamais float : envoyé en JSON sous forme de texte exact, « "2350.00" »
    devise: str = "DH"


class Transaction(BaseModel):
    id: int
    date: datetime
    montant: Decimal  # négatif : sortie d'argent, positif : entrée
    libelle: str


class Facture(BaseModel):
    id: int
    fournisseur: str
    montant: Decimal
    statut: Literal["payee", "impayee"]


class Paiement(BaseModel):
    facture_id: int
    fournisseur: str
    montant: Decimal
    nouveau_solde: Decimal


class DemandeVirement(BaseModel):
    beneficiaire_id: int
    # Refusé automatiquement (422) si nul, négatif ou avec plus de 2 chiffres après la virgule.
    montant: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class Virement(BaseModel):
    beneficiaire: str
    montant: Decimal
    nouveau_solde: Decimal
