"""Retrouver ce que le client désigne avec ses mots : la facture, le bénéficiaire, le montant."""

import re
import unicodedata
from decimal import Decimal, InvalidOperation

# Les fournisseurs, tous fictifs. Le LLM choisit une clé courte, le code la traduit en nom exact.
FOURNISSEURS = {"eau_electricite": "Eau & Électricité (démo)", "internet": "Internet (démo)", "mobile": "Mobile (démo)"}

# Petits mots que le LLM laisse parfois devant le nom : « sifet 500 l Fatima » donne « l Fatima » (l = à, en darija).
PARTICULES = {"l", "li", "le", "la", "a", "ila", "ل"}


def simplifier(texte: str) -> str:
    """« Fatima », « fatima » et « Fâtima » se valent : minuscules, sans accents, sans ponctuation autour."""
    sans_accents = "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
    return sans_accents.lower().strip().strip("!?.,;:، ")


def trouver_beneficiaires(beneficiaires: list[dict], nom: str) -> list[dict]:
    """Les bénéficiaires dont le nom contient tous les mots donnés (« Fatima », « fatima lahlou », « l Fatima »)."""
    mots = [mot for mot in simplifier(nom).replace("'", " ").split() if mot not in PARTICULES]
    if not mots:
        return []
    exacts = [b for b in beneficiaires if simplifier(b["nom"]).split() == mots]
    return exacts or [b for b in beneficiaires if set(mots) <= set(simplifier(b["nom"]).split())]


def lire_montant(valeur) -> Decimal | None:
    """Le montant donné par le LLM (500, « 500 DH », « 1 000,50 ») en Decimal au centime, ou None s'il n'est pas valable.

    On enlève seulement les espaces et « DH » : un « -50 » doit rester négatif, donc refusé, et pas devenir 50.
    """
    texte = re.sub(r"[\s  ]", "", str(valeur)).replace(",", ".")
    texte = re.sub(r"(?i)(dh|mad|dirhams?)$", "", texte)
    try:
        montant = Decimal(texte)
        if not montant.is_finite() or montant != montant.quantize(Decimal("0.01")):  # « NaN », ou 12,345 DH
            return None
        montant = montant.quantize(Decimal("0.01"))
    except InvalidOperation:
        return None
    return montant if montant > 0 else None
