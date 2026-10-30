"""Écrit evals/benchmark/resultats.md à partir des résultats de promptfoo (evals/benchmark/resultats/*.json).

La note de chaque modèle vient du paquet « test » (questions jamais vues). Le paquet « mise au point » est donné à part :
ses questions ont déjà servi à régler Wakil, son score est donc optimiste. Les échecs du paquet test sont publiés.
"""

import json
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

ICI = Path(__file__).resolve().parent
ECRITURES = ["arabe", "latin", "melange", "francais"]


def pourcent(reussis: int, total: int) -> str:
    return f"{100 * reussis / total:.0f} % ({reussis}/{total})" if total else "–"


def lire() -> dict[str, list[dict]]:
    """Les réponses de chaque modèle : question, paquet, écriture, catégorie, réussites, temps, jetons, raison."""
    par_modele = defaultdict(list)
    for fichier in sorted((ICI / "resultats").glob("*.json")):
        for r in json.loads(fichier.read_text())["results"]["results"]:
            v = r["vars"]
            reponse = r.get("response") or {}  # absente si l'appel a échoué (Ollama bloqué…) : compté comme raté
            par_modele[r["provider"]["label"]].append(
                {
                    "question": v["question"],
                    "paquet": v["paquet"],
                    "ecriture": v["ecriture"],
                    "categorie": v["categorie"],
                    "bon_outil": r.get("namedScores", {}).get("bon_outil", 0) == 1,
                    "reussi": bool(r["success"]),
                    "latence": r.get("latencyMs") or reponse.get("latencyMs", 0),
                    "jetons": (reponse.get("tokenUsage") or {}).get("total", 0),
                    "raison": (r.get("gradingResult") or {}).get("reason") or r.get("error", ""),
                    "sortie": reponse.get("output"),
                }
            )
    return par_modele


def tableau_global(par_modele: dict[str, list[dict]]) -> list[str]:
    lignes = [
        "| Modèle | Bon outil (test) | Outil et paramètres justes (test) | Mise au point (outil et paramètres) "
        "| Temps médian | Temps p95 | Jetons par question |",
        "|---|---|---|---|---|---|---|",
    ]
    for modele, reponses in par_modele.items():
        test = [r for r in reponses if r["paquet"] == "test"]
        reglage = [r for r in reponses if r["paquet"] == "mise_au_point"]
        latences = sorted(r["latence"] for r in reponses)
        p95 = latences[min(len(latences) - 1, int(0.95 * len(latences)))] if latences else 0
        lignes.append(
            f"| `{modele}` | {pourcent(sum(r['bon_outil'] for r in test), len(test))} "
            f"| **{pourcent(sum(r['reussi'] for r in test), len(test))}** "
            f"| {pourcent(sum(r['reussi'] for r in reglage), len(reglage))} "
            f"| {statistics.median(latences) / 1000:.1f} s | {p95 / 1000:.1f} s "
            f"| {statistics.mean(r['jetons'] for r in reponses):.0f} |"
        )
    return lignes


def tableau_par(par_modele: dict[str, list[dict]], cle: str, valeurs: list[str]) -> list[str]:
    """Outil et paramètres justes, sur tous les paquets, par écriture ou par catégorie."""
    lignes = ["| Modèle | " + " | ".join(valeurs) + " |", "|---|" + "---|" * len(valeurs)]
    for modele, reponses in par_modele.items():
        cellules = []
        for valeur in valeurs:
            groupe = [r for r in reponses if r[cle] == valeur]
            cellules.append(pourcent(sum(r["reussi"] for r in groupe), len(groupe)))
        lignes.append(f"| `{modele}` | " + " | ".join(cellules) + " |")
    return lignes


def main() -> None:
    par_modele = lire()
    toutes = [r for reponses in par_modele.values() for r in reponses]
    categories = sorted({r["categorie"] for r in toutes})
    nb_test = len({r["question"] for r in toutes if r["paquet"] == "test"})
    nb_reglage = len({r["question"] for r in toutes if r["paquet"] == "mise_au_point"})
    lignes = [
        "# Benchmark darija de Wakil : résultats mesurés",
        "",
        f"Généré le {date.today():%d/%m/%Y} par `evals/benchmark/rapport.py`, à partir de promptfoo. Données 100 % fictives.",
        "",
        "**Ce qui est mesuré** : l'étape 1 de Wakil, par le vrai chemin de l'agent (même prompt, mêmes outils MCP, même "
        "historique). Une réponse est réussie si le LLM choisit le bon outil, avec les paramètres attendus, sans rien "
        "inventer. Aucun outil n'est exécuté.",
        "",
        f"**Les questions** : {nb_test} jamais vues (paquet « test », qui donne la note) et {nb_reglage} déjà utilisées "
        "pour régler Wakil (paquet « mise au point », score optimiste, donné à part).",
        "",
        "## Classement",
        "",
        *tableau_global(par_modele),
        "",
        "## Par écriture (tous paquets)",
        "",
        *tableau_par(par_modele, "ecriture", ECRITURES),
        "",
        "## Par catégorie (tous paquets)",
        "",
        *tableau_par(par_modele, "categorie", categories),
        "",
        "## Échecs du paquet test",
        "",
        "| Modèle | Question | Écriture | Catégorie | Pourquoi |",
        "|---|---|---|---|---|",
    ]
    for modele, reponses in par_modele.items():
        for r in reponses:
            if r["paquet"] == "test" and not r["reussi"]:
                lignes.append(f"| `{modele}` | {r['question']} | {r['ecriture']} | {r['categorie']} | {r['raison']} |")
    (ICI / "resultats.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print("\n".join(lignes[: 14 + len(par_modele)]))


if __name__ == "__main__":
    main()
