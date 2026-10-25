from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Client(BaseModel):
    id: int
    civilite: Literal["madame", "monsieur"]
    prenom: str
    nom: str
    ville: str


class Beneficiaire(BaseModel):
    id: int
    nom: str
    rib_masque: str
    interne: bool  # client de la Banque Atlas Démo ? (sans rien révéler d'autre sur lui)


class Compte(BaseModel):
    id: int
    rib_masque: str  # « •••• 9114 » : le RIB complet ne sort pas de la banque
    plafond_virement: Decimal


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
    simulation: bool  # true : vérification à blanc, rien n'a été payé


class DemandeVirement(BaseModel):
    beneficiaire_id: int
    # Refusé automatiquement (422) si nul, négatif ou avec plus de 2 chiffres après la virgule.
    montant: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

    @field_validator("montant")
    @classmethod
    def au_centime(cls, montant: Decimal) -> Decimal:
        """« 500 » devient « 500.00 », comme tous les montants de l'API (réponse et journal d'audit)."""
        return montant.quantize(Decimal("0.01"))


class Virement(BaseModel):
    beneficiaire: str
    beneficiaire_rib_masque: str
    montant: Decimal
    nouveau_solde: Decimal
    simulation: bool  # true : vérification à blanc, rien n'a été viré


def masquer_rib(rib: str) -> str:
    """« •••• 9114 » : seuls les 4 derniers chiffres du RIB sortent de la banque."""
    return f"•••• {rib[-4:]}"
