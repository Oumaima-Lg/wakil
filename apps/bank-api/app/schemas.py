from datetime import date, datetime
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


class EntreeAudit(BaseModel):
    """Une ligne du journal, lisible par le client : ce qui a été fait sur son compte, et quand."""

    date: datetime
    action: str  # code : paiement_facture, virement, carte_bloquee…
    libelle: str  # « Paiement de la facture Internet (démo) »
    montant: Decimal | None  # positif ; absent pour une action sur une carte


class Carte(BaseModel):
    id: int
    numero_masque: str  # « •••• 4821 » : fictif, jamais le numéro complet
    expiration: str  # « 09/29 »
    statut: Literal["active", "bloquee", "opposee"]
    motif_opposition: Literal["perte", "vol"] | None
    remplacee_par: int | None = None  # après une opposition : l'id de la nouvelle carte


class DemandeOpposition(BaseModel):
    motif: Literal["perte", "vol"]


class Solde(BaseModel):
    compte_id: int
    solde: Decimal  # Decimal, jamais float : envoyé en JSON sous forme de texte exact, « "2350.00" »
    devise: str = "DH"


class Transaction(BaseModel):
    id: int
    date: datetime
    montant: Decimal  # négatif : sortie d'argent, positif : entrée
    libelle: str


class DepensesCategorie(BaseModel):
    categorie: str  # code : « restaurant », « factures »…
    nom: str  # nom affiché : « Restaurant », « Factures »…
    total: Decimal  # positif : l'argent sorti dans cette catégorie
    nombre: int


class Depenses(BaseModel):
    """Ce qui est entré et sorti d'un compte sur une période, calculé par la banque sur toutes ses opérations."""

    du: date
    au: date
    depenses: Decimal  # total des sorties, positif
    entrees: Decimal
    nombre: int  # nombre d'opérations (sorties et entrées)
    par_categorie: list[DepensesCategorie]  # les sorties, de la plus grosse catégorie à la plus petite
    plus_grosse: Transaction | None  # la plus grosse sortie


class Releve(BaseModel):
    """Le relevé d'un mois : solde au début, toutes les opérations dans l'ordre, solde à la fin.

    Toujours vrai : solde_ouverture + total_entrees - total_sorties = solde_cloture."""

    mois: str  # « 2026-09 »
    du: date
    au: date
    complet: bool  # faux pour le mois en cours : d'autres opérations peuvent encore arriver
    solde_ouverture: Decimal
    total_entrees: Decimal
    total_sorties: Decimal  # positif
    solde_cloture: Decimal
    transactions: list[Transaction]  # de la plus ancienne à la plus récente, comme sur un relevé papier


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
