import base64
import calendar
import json
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Path, Query, Request, Response

from app.categories import categorie
from app.db import Connexion
from app.schemas import Depenses, DepensesCategorie, Releve, Solde, Transaction
from app.securite import CompteDuClient

MAROC = ZoneInfo("Africa/Casablanca")
# Une opération appartient au jour qu'elle a eu au Maroc (une opération à 0 h 30 le 1er est du mois qui commence).
JOUR_DU_MAROC = "(date AT TIME ZONE 'Africa/Casablanca')::date"

router = APIRouter(prefix="/comptes", tags=["Comptes"])


@router.get("/{compte_id}/solde")
def consulter_solde(compte: CompteDuClient) -> Solde:
    """Solde actuel d'un compte du client connecté."""
    return Solde(compte_id=compte["id"], solde=compte["solde"])


def curseur_de(ligne: dict) -> str:
    """Le marque-page d'une liste : la dernière opération lue (date et id), en texte opaque pour le client de l'API."""
    position = json.dumps({"date": ligne["date"].isoformat(), "id": ligne["id"]})
    return base64.urlsafe_b64encode(position.encode()).decode()


def position_de(curseur: str) -> tuple[datetime, int]:
    try:
        position = json.loads(base64.urlsafe_b64decode(curseur.encode()))
        return datetime.fromisoformat(position["date"]), int(position["id"])
    except (ValueError, KeyError, TypeError) as erreur:
        raise HTTPException(status_code=422, detail="Curseur invalide") from erreur


@router.get("/{compte_id}/transactions")
def lister_transactions(
    compte: CompteDuClient,
    conn: Connexion,
    request: Request,
    response: Response,
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
    du: date | None = None,
    au: date | None = None,
    curseur: Annotated[str | None, Query(description="Le marque-page de la page précédente (en-tête Link)")] = None,
) -> list[Transaction]:
    """Opérations d'un compte du client connecté, de la plus récente à la plus ancienne, entre deux dates incluses
    (jours du Maroc) si on les donne.

    Page par page : s'il en reste, l'en-tête Link (RFC 8288) donne l'adresse de la page suivante (rel="next"). Le
    curseur retient la dernière opération lue : si une opération arrive entre deux pages, rien n'est sauté ni répété."""
    if du and au and du > au:
        raise HTTPException(status_code=422, detail="La date de début doit précéder la date de fin")
    conditions, valeurs = ["compte_id = %s"], [compte["id"]]
    if du:
        conditions.append(f"{JOUR_DU_MAROC} >= %s")
        valeurs.append(du)
    if au:
        conditions.append(f"{JOUR_DU_MAROC} <= %s")
        valeurs.append(au)
    if curseur:
        conditions.append("(date, id) < (%s, %s)")
        valeurs += list(position_de(curseur))
    lignes = conn.execute(
        f"SELECT id, date, montant, libelle FROM transactions WHERE {' AND '.join(conditions)}"
        " ORDER BY date DESC, id DESC LIMIT %s",
        (*valeurs, limite + 1),  # une de plus : pour savoir s'il reste une page
    ).fetchall()
    if len(lignes) > limite:
        lignes = lignes[:limite]
        suivante = request.url.include_query_params(curseur=curseur_de(lignes[-1]))
        response.headers["Link"] = f'<{suivante}>; rel="next"'
    return [Transaction(**ligne) for ligne in lignes]


@router.get("/{compte_id}/transactions/{transaction_id}")
def detail_transaction(transaction_id: int, compte: CompteDuClient, conn: Connexion) -> Transaction:
    """Une opération d'un compte du client connecté. 404 si elle est d'un autre compte : on ne révèle pas qu'elle existe."""
    ligne = conn.execute(
        "SELECT id, date, montant, libelle FROM transactions WHERE id = %s AND compte_id = %s",
        (transaction_id, compte["id"]),
    ).fetchone()
    if ligne is None:
        raise HTTPException(status_code=404, detail="Opération introuvable")
    return Transaction(**ligne)


@router.get("/{compte_id}/releves/{mois}")
def releve_mensuel(
    compte: CompteDuClient,
    conn: Connexion,
    mois: Annotated[str, Path(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Le mois, « 2026-09 »")],
) -> Releve:
    """Le relevé d'un mois (jours du Maroc) : solde au début, opérations, totaux, solde à la fin.

    La banque ne garde que le solde actuel : le solde de fin de mois est le solde actuel moins tout ce qui s'est
    passé après le mois, et le solde de début est celui de fin moins les opérations du mois."""
    annee, numero = map(int, mois.split("-"))
    du = date(annee, numero, 1)
    au = date(annee, numero, calendar.monthrange(annee, numero)[1])
    aujourd_hui = datetime.now(MAROC).date()
    if du > aujourd_hui:
        raise HTTPException(status_code=404, detail="Pas encore de relevé pour ce mois")
    lignes = conn.execute(
        f"SELECT id, date, montant, libelle FROM transactions WHERE compte_id = %s AND {JOUR_DU_MAROC} BETWEEN %s AND %s"
        " ORDER BY date, id",
        (compte["id"], du, au),
    ).fetchall()
    apres = conn.execute(
        f"SELECT coalesce(sum(montant), 0) AS total FROM transactions WHERE compte_id = %s AND {JOUR_DU_MAROC} > %s",
        (compte["id"], au),
    ).fetchone()["total"]
    entrees = sum((ligne["montant"] for ligne in lignes if ligne["montant"] > 0), Decimal("0.00"))
    sorties = sum((-ligne["montant"] for ligne in lignes if ligne["montant"] < 0), Decimal("0.00"))
    cloture = compte["solde"] - apres
    return Releve(
        mois=mois,
        du=du,
        au=au,
        complet=au < aujourd_hui,
        solde_ouverture=cloture - entrees + sorties,
        total_entrees=entrees,
        total_sorties=sorties,
        solde_cloture=cloture,
        transactions=[Transaction(**ligne) for ligne in lignes],
    )


@router.get("/{compte_id}/depenses")
def resumer_depenses(compte: CompteDuClient, conn: Connexion, du: date, au: date) -> Depenses:
    """Ce qui est entré et sorti d'un compte du client connecté entre deux dates incluses (jours du Maroc), avec les
    sorties par catégorie et la plus grosse d'entre elles.

    Calculé sur toutes les opérations de la période, sans limite : un total ne doit jamais oublier une ligne."""
    if du > au:
        raise HTTPException(status_code=422, detail="La date de début doit précéder la date de fin")
    lignes = conn.execute(
        "SELECT id, date, montant, libelle FROM transactions"
        f" WHERE compte_id = %s AND {JOUR_DU_MAROC} BETWEEN %s AND %s"
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
