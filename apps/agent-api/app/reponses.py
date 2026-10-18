"""Les phrases de Wakil. Les montants viennent de la banque et sont écrits par ce code, jamais par le LLM."""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

MAROC = ZoneInfo("Africa/Casablanca")

SALUT = "Wa 3alikom salam ! Ana Wakil, l'assistant dyal Banque Atlas Démo. Kifach n9der n3awnek ?"
REFUS = (
    "Smeh lia, ana ghir l'assistant dyal Banque Atlas Démo : n9der n3awnek f solde, l'opérations w les factures dyalek."
)
ERREUR = "Smeh lia, kayn mochkil f la banque daba. 3awed men ba3d."


def dh(montant: str | Decimal) -> str:
    """Montant à la marocaine : « 2 350 DH », « -57,98 DH »."""
    texte = f"{Decimal(montant):,.2f}".replace(",", " ").replace(".", ",")
    return f"{texte.removesuffix(',00')} DH"


def solde(resultat: dict) -> str:
    return f"Solde dyalek howa {dh(resultat['solde'])}."


def transactions(resultat: list[dict]) -> str:
    lignes = [
        f"- {datetime.fromisoformat(t['date']).astimezone(MAROC):%d/%m} · {t['libelle']} : {dh(t['montant'])}"
        for t in resultat
    ]
    return "Hahoma akhir l'opérations dyalek :\n" + "\n".join(lignes)


def factures(resultat: list[dict]) -> str:
    if not resultat:
        return "Ma 3ndek hta facture mazal ma tkhelsat."
    lignes = [f"- {f['fournisseur']} : {dh(f['montant'])}" for f in resultat]
    if len(resultat) == 1:
        return "3ndek facture wa7da mazal ma tkhelsat :\n" + lignes[0]
    total = sum(Decimal(f["montant"]) for f in resultat)
    return f"3ndek {len(resultat)} factures mazal ma tkhelsou ({dh(total)} f lmjmou3) :\n" + "\n".join(lignes)
