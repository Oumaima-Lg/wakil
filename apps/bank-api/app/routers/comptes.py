from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.categories import categorie
from app.db import Connexion
from app.schemas import Depenses, DepensesCategorie, Solde, Transaction
from app.securite import CompteDuClient

router = APIRouter(prefix="/comptes", tags=["Comptes"])


@router.get("/{compte_id}/solde")
def consulter_solde(compte: CompteDuClient) -> Solde:
    """Solde actuel d'un compte du client connecté."""
    return Solde(compte_id=compte["id"], solde=compte["solde"])


@router.get("/{compte_id}/transactions")
def lister_transactions(
    compte: CompteDuClient,
    conn: Connexion,
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[Transaction]:
    """Dernières opérations d'un compte du client connecté, de la plus récente à la plus ancienne."""
    lignes = conn.execute(
        "SELECT id, date, montant, libelle FROM transactions WHERE compte_id = %s ORDER BY date DESC, id DESC LIMIT %s",
        (compte["id"], limite),
    ).fetchall()
    return [Transaction(**ligne) for ligne in lignes]


@router.get("/{compte_id}/depenses")
def resumer_depenses(compte: CompteDuClient, conn: Connexion, du: date, au: date) -> Depenses:
    """Ce qui est entré et sorti d'un compte du client connecté entre deux dates incluses (jours du Maroc), avec les
    sorties par catégorie et la plus grosse d'entre elles.

    Calculé sur toutes les opérations de la période, sans limite : un total ne doit jamais oublier une ligne."""
    if du > au:
        raise HTTPException(status_code=422, detail="La date de début doit précéder la date de fin")
    lignes = conn.execute(
        "SELECT id, date, montant, libelle FROM transactions"
        " WHERE compte_id = %s AND (date AT TIME ZONE 'Africa/Casablanca')::date BETWEEN %s AND %s"
        " ORDER BY date DESC, id DESC",
        (compte["id"], du, au),
    ).fetchall()
    sorties = [ligne for ligne in lignes if ligne["montant"] < 0]
    par_categorie: dict[tuple[str, str], list[Decimal]] = defaultdict(list)
    for ligne in sorties:
        par_categorie[categorie(ligne["libelle"])].append(-ligne["montant"])
    categories = [
        DepensesCategorie(categorie=code, nom=nom, total=sum(montants), nombre=len(montants))
        for (code, nom), montants in par_categorie.items()
    ]
    plus_grosse = min(sorties, key=lambda ligne: ligne["montant"], default=None)
    return Depenses(
        du=du,
        au=au,
        depenses=sum((-ligne["montant"] for ligne in sorties), Decimal("0.00")),
        entrees=sum((ligne["montant"] for ligne in lignes if ligne["montant"] > 0), Decimal("0.00")),
        nombre=len(lignes),
        par_categorie=sorted(categories, key=lambda c: c.total, reverse=True),
        plus_grosse=Transaction(**plus_grosse) if plus_grosse else None,
    )
