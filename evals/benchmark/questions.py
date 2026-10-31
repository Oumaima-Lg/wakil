"""Les questions du benchmark, lues dans nos fichiers et données à promptfoo (tests: file://questions.py:creer_tests).

Deux paquets :
- « test » : les questions jamais vues, qui notent Wakil (data/benchmark/questions-*.yaml) ;
- « mise_au_point » : les questions qui ont déjà servi à régler Wakil, pour qu'elles ne faussent pas la note. Ce sont
  les questions de evals/faq/questions.yaml, toute phrase qui apparaît déjà dans les conversations annotées
  (data/benchmark/annotations.md) ou dans les questions types de la FAQ (data/faq/faq.yaml), et les questions marquées
  « deja_vue » (Wakil a été corrigé après avoir vu leur échec).
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[2]
CATEGORIES = {"solde", "plafond", "operations", "factures", "paiement", "virement", "faq", "floue", "hors_sujet",
              "suite", "non_disponible", "beneficiaires", "depenses", "plusieurs"}  # fmt: skip
OUTILS = {"consulter_solde", "consulter_plafond", "lister_transactions", "lister_factures", "lister_beneficiaires",
          "analyser_depenses", "payer_facture", "faire_virement", "question_faq", None}  # fmt: skip
AUCUN = "aucun"  # « aucun outil » : promptfoo refuse une variable null


def en_texte(liste: list) -> str:
    """Une liste passée à promptfoo en texte JSON : une variable qui contient une liste deviendrait un test par élément."""
    return json.dumps(liste, ensure_ascii=False)


CATEGORIE_DE_L_OUTIL = {"consulter_solde": "solde", "lister_transactions": "operations", "lister_factures": "factures",
                        "payer_facture": "paiement", "faire_virement": "virement"}  # fmt: skip


def simplifier(texte: str) -> str:
    """Pour comparer deux phrases : minuscules, sans accents ni ponctuation, espaces réduits."""
    sans_accents = "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^\w\s]", " ", sans_accents.lower()).split())


def _deja_vues() -> set[str]:
    """Les phrases qui ont déjà servi à régler Wakil."""
    vues = {
        simplifier(q)
        for fiche in yaml.safe_load((RACINE / "data/faq/faq.yaml").read_text())
        for q in fiche["questions"]
    }
    for ligne in (RACINE / "data/benchmark/annotations.md").read_text().splitlines():
        cellules = [c.strip() for c in ligne.split("|")]
        if len(cellules) > 3 and cellules[1].isdigit():  # | n° | message | …
            vues.add(simplifier(cellules[2]))
    return vues


def _questions_de_la_faq() -> list[dict]:
    """evals/faq/questions.yaml, au format du benchmark (toutes déjà vues : mise au point)."""
    questions = []
    for q in yaml.safe_load((RACINE / "evals/faq/questions.yaml").read_text()):
        if q["fiche"]:
            outil, categorie = "question_faq", "faq"
        else:
            outil = q.get("outil")
            categorie = CATEGORIE_DE_L_OUTIL.get(outil, "hors_sujet")
        questions.append({**q, "outil": outil, "categorie": categorie, "arguments": {}, "source": "evals/faq"})
    return questions


def creer_tests(config: dict | None = None) -> list[dict]:
    vues = _deja_vues()
    questions = _questions_de_la_faq()
    for fichier in sorted((RACINE / "data/benchmark").glob("questions-*.yaml")):
        auteur = fichier.stem.removeprefix("questions-")
        questions += [{**q, "source": auteur} for q in yaml.safe_load(fichier.read_text()) or []]

    tests = []
    for q in questions:
        # Une question qu'on ne sait pas encore noter (catégorie ou outil inconnus) est mise de côté, et signalée.
        # Plusieurs demandes dans un même message : la liste des outils attendus.
        attendus = q.get("outil") if isinstance(q.get("outil"), list) else [q.get("outil")]
        if q["categorie"] not in CATEGORIES or not set(attendus) <= OUTILS:
            print(f"Question mise de côté ({q['categorie']} / {q.get('outil')}) : {q['question']}", file=sys.stderr)
            continue
        deja_vue = q["source"] == "evals/faq" or q.get("deja_vue") or simplifier(q["question"]) in vues
        paquet = "mise_au_point" if deja_vue else "test"
        variables = {
            "question": q["question"],
            "avant": en_texte(q.get("avant") or []),
            "categorie": q["categorie"],
            "ecriture": q["ecriture"],
            "outil": en_texte(attendus) if isinstance(q.get("outil"), list) else q.get("outil") or AUCUN,
            "arguments": q.get("arguments") or {},
            "paquet": paquet,
            "source": q["source"],
        }
        tests.append(
            {
                "description": q["question"],
                "vars": variables,
                "metadata": {"categorie": q["categorie"], "ecriture": q["ecriture"], "paquet": paquet},
                "assert": [{"type": "python", "value": "file://verifier.py"}],
            }
        )
    return tests


if __name__ == "__main__":
    tests = creer_tests()
    for paquet in ("test", "mise_au_point"):
        print(paquet, sum(t["vars"]["paquet"] == paquet for t in tests))
