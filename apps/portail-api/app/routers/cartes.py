"""Les actions sur la carte dans l'espace : bloquer, débloquer, faire opposition, puis commander une nouvelle carte.

Wakil, lui, peut seulement bloquer (décision du 31/10/2026) : une injection de prompt ou un voleur ne peut pas réactiver
une carte par le chat.
Le client vient de la session ; le cookie de session (SameSite=Lax) n'est pas envoyé par un POST venant d'un autre
site, ce qui protège ces routes contre le CSRF. La banque vérifie l'état de la carte et écrit le journal d'audit.
"""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app import banque
from app.session import ClientConnecte

router = APIRouter(prefix="/moi/cartes", tags=["cartes"])


class DemandeOpposition(BaseModel):
    motif: Literal["perte", "vol"]


@router.post("/{carte_id}/blocage")
def bloquer(carte_id: int, client_id: ClientConnecte) -> dict:
    """Bloque temporairement la carte (réversible). Tant qu'elle est bloquée, Wakil reste en mode sécurité."""
    return banque.bloquer_carte(client_id, carte_id)


@router.post("/{carte_id}/deblocage")
def debloquer(carte_id: int, client_id: ClientConnecte) -> dict:
    """Débloque une carte bloquée (une carte en opposition ne se débloque jamais : refus 409 de la banque)."""
    return banque.debloquer_carte(client_id, carte_id)


@router.post("/{carte_id}/opposition")
def faire_opposition(carte_id: int, demande: DemandeOpposition, client_id: ClientConnecte) -> dict:
    """Met la carte en opposition, pour perte ou vol : définitif."""
    return banque.faire_opposition(client_id, carte_id, demande.motif)


@router.post("/{carte_id}/remplacement")
def commander_nouvelle_carte(carte_id: int, client_id: ClientConnecte) -> dict:
    """Commande une nouvelle carte après une opposition (une seule fois) : la banque crée la carte et écrit le journal."""
    return banque.remplacer_carte(client_id, carte_id)
