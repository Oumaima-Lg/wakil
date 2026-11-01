"""Le juge du benchmark, appelé par promptfoo pour chaque réponse : réussi ou raté, sans juge LLM.

Réussi si le LLM a choisi le bon outil, avec les arguments attendus, et sans rien inventer :
- fournisseur : la même valeur ;
- montant : le même nombre (« 300 », « 300 DH », 300.0) ;
- bénéficiaire : chaque mot attendu se retrouve dans le nom choisi (« Fatima » dans « l Fatima ») ;
- mois des dépenses : le même ; oublié, il vaut « ce_mois » (la valeur par défaut de l'outil) ;
- mois d'un relevé (1 à 12) : le même nombre ; il est inventé si la phrase ne contient ni ce nombre ni le nom du mois ;
- carte : les 4 derniers chiffres attendus se retrouvent dans ce que le modèle a écrit ;
- invention : un argument que le client n'a pas donné (un bénéficiaire ou un montant absent de sa phrase, une catégorie
  de dépenses qu'il n'a pas nommée, ou tout argument d'une demande floue) fait échouer.

Plusieurs demandes dans un même message : les outils attendus forment une liste, et c'est l'ensemble des outils que
Wakil va lire qui est comparé (sans leurs arguments).
"""

import json
import re
from decimal import Decimal, InvalidOperation

from questions import AUCUN, simplifier

PARTICULES = {"l", "li", "le", "la", "a", "ila", "f"}
# Les noms des mois, en français et en arabe marocain : un mois de relevé est inventé si la phrase n'en contient aucun.
NOMS_DES_MOIS = [
    ("janvier", "يناير"), ("fevrier", "فبراير"), ("mars", "مارس"), ("avril", "أبريل"), ("mai", "ماي"),
    ("juin", "يونيو"), ("juillet", "يوليوز"), ("aout", "غشت"), ("septembre", "شتنبر"), ("octobre", "أكتوبر"),
    ("novembre", "نونبر"), ("decembre", "دجنبر"),
]  # fmt: skip


def _montant(valeur) -> Decimal | None:
    texte = re.sub(r"(?i)\s|dh|mad|dirhams?", "", str(valeur)).replace(",", ".")
    try:
        return Decimal(texte)
    except InvalidOperation:
        return None


def _mots(texte) -> set[str]:
    return {m for m in simplifier(str(texte)).split() if m not in PARTICULES}


def _argument_juste(nom: str, attendu, obtenu) -> bool:
    if nom == "periode" and obtenu is None:
        obtenu = "ce_mois"
    if obtenu is None:
        return False
    if nom == "montant":
        return _montant(obtenu) is not None and _montant(obtenu) == _montant(attendu)
    if nom == "beneficiaire":
        return _mots(attendu) <= _mots(obtenu)
    if nom == "mois":
        return str(obtenu).strip().isdigit() and int(obtenu) == int(attendu)
    if nom == "carte":
        return str(attendu) in re.sub(r"\D", "", str(obtenu))
    return str(obtenu) == str(attendu)


def _invente(nom: str, obtenu, question: str) -> bool:
    """Un bénéficiaire ou un montant que le client n'a jamais écrit."""
    if nom == "beneficiaire":
        return bool(_mots(obtenu)) and not _mots(obtenu) <= _mots(question)
    if nom == "montant":
        nombre = _montant(obtenu)
        return nombre is not None and f"{nombre.normalize():f}" not in re.sub(r"[\s ]", "", question)
    if nom == "mois":
        if not str(obtenu).strip().isdigit() or not 1 <= int(obtenu) <= 12:
            return True
        phrase = simplifier(question)
        return str(int(obtenu)) not in re.findall(r"\d+", phrase) and not any(
            simplifier(nom_du_mois) in phrase for nom_du_mois in NOMS_DES_MOIS[int(obtenu) - 1]
        )
    return nom in ("categorie", "carte")  # une catégorie ou une carte non attendue : le client n'en a nommé aucune


def get_assert(output, context) -> dict:
    sortie = json.loads(output) if isinstance(output, str) else output
    variables = context["vars"]
    attendu_outil = None if variables.get("outil") == AUCUN else variables.get("outil")
    if attendu_outil is not None and attendu_outil.startswith(
        "["
    ):  # plusieurs outils, en texte JSON (questions.en_texte)
        attendu_outil = json.loads(attendu_outil)
    if isinstance(attendu_outil, list):
        lus = sortie.get("outils") or []
        bon_outil = set(lus) == set(attendu_outil)
        raison = "réussi" if bon_outil else f"outils {lus} au lieu de {attendu_outil}"
        score = 1.0 if bon_outil else 0.0
        return {"pass": bon_outil, "score": score, "reason": raison,
                "named_scores": {"bon_outil": score, "bons_arguments": score}}  # fmt: skip
    bon_outil = sortie.get("outil") == attendu_outil
    raisons = [] if bon_outil else [f"outil {sortie.get('outil')} au lieu de {attendu_outil}"]

    arguments = sortie.get("arguments") or {}
    for nom, valeur in (variables.get("arguments") or {}).items():
        if not _argument_juste(nom, valeur, arguments.get(nom)):
            raisons.append(f"{nom} = {arguments.get(nom)!r} au lieu de {valeur!r}")
    for nom, valeur in arguments.items():
        if nom in (variables.get("arguments") or {}) or valeur in (None, ""):
            continue
        # Une demande floue : rien ne doit être deviné, Wakil demandera le reste.
        if variables.get("categorie") == "floue" or _invente(nom, valeur, variables["question"]):
            raisons.append(f"{nom} inventé : {valeur!r}")
    bons_arguments = bon_outil and len(raisons) == 0

    return {
        "pass": bons_arguments,
        "score": 1.0 if bons_arguments else 0.0,
        "reason": "réussi" if bons_arguments else " ; ".join(raisons),
        "named_scores": {"bon_outil": 1.0 if bon_outil else 0.0, "bons_arguments": 1.0 if bons_arguments else 0.0},
    }
