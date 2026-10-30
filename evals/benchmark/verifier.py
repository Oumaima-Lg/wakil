"""Le juge du benchmark, appelé par promptfoo pour chaque réponse : réussi ou raté, sans juge LLM.

Réussi si le LLM a choisi le bon outil, avec les arguments attendus, et sans rien inventer :
- fournisseur : la même valeur ;
- montant : le même nombre (« 300 », « 300 DH », 300.0) ;
- bénéficiaire : chaque mot attendu se retrouve dans le nom choisi (« Fatima » dans « l Fatima ») ;
- invention : un argument que le client n'a pas donné (un bénéficiaire ou un montant absent de sa phrase) fait échouer.
"""

import json
import re
from decimal import Decimal, InvalidOperation

from questions import simplifier

PARTICULES = {"l", "li", "le", "la", "a", "ila", "f"}


def _montant(valeur) -> Decimal | None:
    texte = re.sub(r"(?i)\s|dh|mad|dirhams?", "", str(valeur)).replace(",", ".")
    try:
        return Decimal(texte)
    except InvalidOperation:
        return None


def _mots(texte) -> set[str]:
    return {m for m in simplifier(str(texte)).split() if m not in PARTICULES}


def _argument_juste(nom: str, attendu, obtenu) -> bool:
    if obtenu is None:
        return False
    if nom == "montant":
        return _montant(obtenu) is not None and _montant(obtenu) == _montant(attendu)
    if nom == "beneficiaire":
        return _mots(attendu) <= _mots(obtenu)
    return str(obtenu) == str(attendu)


def _invente(nom: str, obtenu, question: str) -> bool:
    """Un bénéficiaire ou un montant que le client n'a jamais écrit."""
    if nom == "beneficiaire":
        return bool(_mots(obtenu)) and not _mots(obtenu) <= _mots(question)
    if nom == "montant":
        nombre = _montant(obtenu)
        return nombre is not None and f"{nombre.normalize():f}" not in re.sub(r"[\s ]", "", question)
    return False


def get_assert(output, context) -> dict:
    sortie = json.loads(output) if isinstance(output, str) else output
    variables = context["vars"]
    attendu_outil = variables.get("outil")
    bon_outil = sortie.get("outil") == attendu_outil
    raisons = [] if bon_outil else [f"outil {sortie.get('outil')} au lieu de {attendu_outil}"]

    arguments = sortie.get("arguments") or {}
    for nom, valeur in (variables.get("arguments") or {}).items():
        if not _argument_juste(nom, valeur, arguments.get(nom)):
            raisons.append(f"{nom} = {arguments.get(nom)!r} au lieu de {valeur!r}")
    for nom, valeur in arguments.items():
        if nom not in (variables.get("arguments") or {}) and _invente(nom, valeur, variables["question"]):
            raisons.append(f"{nom} inventé : {valeur!r}")
    bons_arguments = bon_outil and len(raisons) == 0

    return {
        "pass": bons_arguments,
        "score": 1.0 if bons_arguments else 0.0,
        "reason": "réussi" if bons_arguments else " ; ".join(raisons),
        "named_scores": {"bon_outil": 1.0 if bon_outil else 0.0, "bons_arguments": 1.0 if bons_arguments else 0.0},
    }
