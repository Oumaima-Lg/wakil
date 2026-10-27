"""Mesure l'étape 1 de Wakil, le choix de l'outil par le LLM, sur les questions de test (evals/faq/questions.yaml).

Chaque question est envoyée au vrai LLM, avec le prompt système et les outils de Wakil, dans une conversation neuve.
On note l'outil choisi, sans rien exécuter : ni la banque ni la FAQ ne sont appelées.
Attendu : question_faq pour une question de FAQ, l'outil du compte pour une demande sur le compte, aucun outil pour le
hors-sujet.

Lancer depuis apps/agent-api (Ollama et le serveur MCP démarrés) :
  uv run --env-file ../../.env python ../../evals/faq/routage.py
Écrit evals/faq/routage.md.
"""

import statistics
import sys
import time
from pathlib import Path

import yaml

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "apps" / "agent-api"))  # le code de l'agent, sans le copier

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402

from app import agent  # noqa: E402


def attendu(question: dict) -> str | None:
    return agent.OUTIL_FAQ if question["fiche"] else question.get("outil")


def choisir(llm, texte: str) -> str | None:
    """L'outil que le LLM choisit pour ce message, comme la case « comprendre » du graphe."""
    message = llm.invoke([SystemMessage(agent.SYSTEME), HumanMessage(texte)])
    return message.tool_calls[0]["name"] if message.tool_calls else None


def pourcent(n: int, total: int) -> str:
    return f"{100 * n / total:.0f} % ({n}/{total})" if total else "–"


def mesurer() -> str:
    questions = yaml.safe_load((ICI / "questions.yaml").read_text(encoding="utf-8"))
    llm = agent.le_llm()
    resultats, durees = [], []
    for q in questions:
        debut = time.perf_counter()
        resultats.append({**q, "attendu": attendu(q), "obtenu": choisir(llm, q["question"])})
        durees.append(time.perf_counter() - debut)

    groupes = {
        "Questions de FAQ → question_faq": [r for r in resultats if r["fiche"]],
        "Demandes sur le compte → leur outil": [r for r in resultats if not r["fiche"] and r.get("outil")],
        "Hors sujet → aucun outil": [r for r in resultats if not r["fiche"] and not r.get("outil")],
    }
    lignes = [
        "# Choix de l'outil par le LLM : résultats mesurés",
        "",
        f"LLM : `{agent.le_llm().bound.model}` · {len(resultats)} questions · généré par `evals/faq/routage.py`. "
        "Seul le choix de l'outil est mesuré (étape 1) : ni la banque ni la FAQ ne sont appelées.",
        "",
        "| Groupe | Bon outil choisi |",
        "|---|---|",
    ]
    for nom, groupe in groupes.items():
        lignes.append(f"| {nom} | {pourcent(sum(r['obtenu'] == r['attendu'] for r in groupe), len(groupe))} |")
    faq_par_ecriture = {}
    for r in groupes["Questions de FAQ → question_faq"]:
        faq_par_ecriture.setdefault(r["ecriture"], []).append(r["obtenu"] == r["attendu"])
    lignes += ["", "Questions de FAQ envoyées à `question_faq`, par écriture :", ""]
    lignes += [f"- {ecriture} : {pourcent(sum(v), len(v))}" for ecriture, v in faq_par_ecriture.items()]
    lignes += [
        "",
        f"Temps du choix (un appel au LLM) : médiane {statistics.median(durees):.1f} s, maximum {max(durees):.1f} s.",
        "",
        "## Détail",
        "",
        "| Question | Écriture | Attendu | Obtenu | |",
        "|---|---|---|---|---|",
    ]
    for r in resultats:
        signe = "✅" if r["obtenu"] == r["attendu"] else "❌"
        lignes.append(
            f"| {r['question']} | {r['ecriture']} | {r['attendu'] or '(aucun)'} | {r['obtenu'] or '(aucun)'} | {signe} |"
        )
    return "\n".join(lignes) + "\n"


if __name__ == "__main__":
    rapport = mesurer()
    (ICI / "routage.md").write_text(rapport, encoding="utf-8")
    print(rapport)
