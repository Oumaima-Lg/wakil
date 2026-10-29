"""Mesure la recherche dans la FAQ sur les questions de test (evals/faq/questions.yaml), qui sont différentes des
questions écrites dans les fiches.

Lancer depuis apps/rag-faq (base et Ollama démarrés, FAQ indexée avec python -m app.faq) :
  uv run --env-file ../../.env python ../../evals/faq/mesurer.py
Écrit evals/faq/resultats.md : chiffres par écriture, choix du seuil, et le détail de chaque question (échecs compris).
"""

import statistics
import sys
import time
from pathlib import Path

import yaml

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "apps" / "rag-faq"))  # le code du service de la FAQ, sans le copier

from app import faq  # noqa: E402

ECRITURES = {
    "arabe": "Lettres arabes",
    "latin": "Lettres latines",
    "melange": "Mélange darija et français",
    "francais": "Français",
}
SEUILS = [round(0.40 + 0.05 * i, 2) for i in range(10)]  # de 0,40 à 0,85


def pourcent(n: int, total: int) -> str:
    return f"{100 * n / total:.0f} % ({n}/{total})" if total else "–"


def mesurer() -> str:
    questions = yaml.safe_load((ICI / "questions.yaml").read_text(encoding="utf-8"))
    connues = {f["id"] for f in faq.lire_fiches()}
    phrases_des_fiches = {q for f in faq.lire_fiches() for q in f["questions"]}
    for q in questions:  # garde-fous : la mesure ne doit ni tricher ni viser une fiche qui n'existe pas
        assert q["question"] not in phrases_des_fiches, f"Fuite : « {q['question']} » est aussi dans faq.yaml"
        assert q["fiche"] is None or q["fiche"] in connues, f"Fiche inconnue : {q['fiche']}"

    resultats, durees = [], []
    for q in questions:
        debut = time.perf_counter()
        classement = faq.classer(q["question"], 3)
        durees.append(time.perf_counter() - debut)
        resultats.append({**q, "classement": classement})

    de_faq = [r for r in resultats if r["fiche"]]
    hors_faq = [r for r in resultats if not r["fiche"]]
    lignes = [
        "# Recherche dans la FAQ : résultats mesurés",
        "",
        f"Modèle d'embeddings : `{faq.MODELE}` · {len(connues)} fiches · {len(de_faq)} questions de FAQ et "
        f"{len(hors_faq)} questions qui n'en sont pas · seuil actuel dans `app/faq.py` : {faq.SEUIL:.2f}",
        "",
        "Généré par `evals/faq/mesurer.py`. **hit@1** : la bonne fiche arrive en premier. **hit@3** : elle est dans les "
        "trois premières. Les questions de test sont différentes des questions types écrites dans les fiches.",
        "",
        "## Par écriture",
        "",
        "| Écriture | hit@1 | hit@3 |",
        "|---|---|---|",
    ]
    for code, nom in ECRITURES.items():
        groupe = [r for r in de_faq if r["ecriture"] == code]
        hit1 = sum(r["classement"][0].fiche == r["fiche"] for r in groupe)
        hit3 = sum(r["fiche"] in [t.fiche for t in r["classement"]] for r in groupe)
        lignes.append(f"| {nom} | {pourcent(hit1, len(groupe))} | {pourcent(hit3, len(groupe))} |")
    hit1 = sum(r["classement"][0].fiche == r["fiche"] for r in de_faq)
    hit3 = sum(r["fiche"] in [t.fiche for t in r["classement"]] for r in de_faq)
    lignes += [f"| **Total** | **{pourcent(hit1, len(de_faq))}** | **{pourcent(hit3, len(de_faq))}** |", ""]

    lignes += [
        "## Choix du seuil",
        "",
        "Pour chaque seuil : ce que Wakil ferait. Une question de FAQ est **bien servie** si la première fiche est la "
        "bonne et dépasse le seuil ; **mal servie** si une mauvaise fiche dépasse le seuil (Wakil cite un texte qui "
        "ne répond pas) ; **sans réponse** sinon. Une question hors FAQ ne doit jamais dépasser le seuil.",
        "",
        "| Seuil | FAQ bien servie | FAQ mal servie | FAQ sans réponse | Hors FAQ servie à tort |",
        "|---|---|---|---|---|",
    ]
    for seuil in SEUILS:
        bien = sum(r["classement"][0].fiche == r["fiche"] and r["classement"][0].similarite >= seuil for r in de_faq)
        mal = sum(r["classement"][0].fiche != r["fiche"] and r["classement"][0].similarite >= seuil for r in de_faq)
        sans = len(de_faq) - bien - mal
        a_tort = sum(r["classement"][0].similarite >= seuil for r in hors_faq)
        lignes.append(
            f"| {seuil:.2f} | {pourcent(bien, len(de_faq))} | {pourcent(mal, len(de_faq))} | "
            f"{pourcent(sans, len(de_faq))} | {pourcent(a_tort, len(hors_faq))} |"
        )
    scores_bons = [r["classement"][0].similarite for r in de_faq if r["classement"][0].fiche == r["fiche"]]
    scores_hors = [r["classement"][0].similarite for r in hors_faq]
    lignes += [
        "",
        f"Meilleur score d'une question hors FAQ : **{max(scores_hors):.2f}**. Plus faible score d'une question de FAQ "
        f"bien classée : **{min(scores_bons):.2f}**."
        if scores_bons and scores_hors
        else "",
        "",
        f"Temps de recherche (vecteur de la question + requête pgvector) : médiane "
        f"{1000 * statistics.median(durees):.0f} ms, maximum {1000 * max(durees):.0f} ms.",
        "",
        "## Détail de chaque question",
        "",
        "| Question | Écriture | Attendu | 1re fiche (score) | 2e | 3e | |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in resultats:
        c = r["classement"]
        juste = (c[0].fiche == r["fiche"]) if r["fiche"] else None
        signe = "✅" if juste else "❌" if juste is False else "·"
        cellules = [f"{t.fiche} ({t.similarite:.2f})" for t in c] + [""] * (3 - len(c))
        lignes.append(
            f"| {r['question']} | {r['ecriture']} | {r['fiche'] or '(hors FAQ)'} | "
            + " | ".join(cellules)
            + f" | {signe} |"
        )
    return "\n".join(lignes) + "\n"


if __name__ == "__main__":
    rapport = mesurer()
    (ICI / "resultats.md").write_text(rapport, encoding="utf-8")
    print(rapport)
