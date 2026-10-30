"""Fournisseur promptfoo : l'étape 1 de Wakil (le LLM choisit l'outil et ses paramètres), par le vrai chemin de l'agent.

Le même prompt système, les mêmes outils (annoncés par les serveurs MCP, qui doivent tourner) et le même format
d'historique que la case « comprendre » d'agent-api. Aucun outil n'est exécuté : ni la banque ni la FAQ ne sont
appelées. Le modèle vient de la configuration du fournisseur (config: modele: …).

Pour une question de suite, les messages d'avant passent d'abord par le même LLM : l'historique contient alors les
outils qu'il a vraiment choisis, comme dans une conversation réelle.
"""

import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "apps" / "agent-api"))  # le code de l'agent, sans le copier

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402

from app import agent, outils  # noqa: E402

CONNUS = {*agent.OUTILS, *agent.OPERATIONS, agent.OUTIL_FAQ}
_llms: dict[str, object] = {}  # un LLM par modèle, créé une fois par processus


def _llm(modele: str):
    if modele not in _llms:
        descriptions, _ = outils.descriptions_pour_le_llm({*agent.OUTILS, agent.OUTIL_FAQ}, set(agent.OPERATIONS))
        _llms[modele] = ChatOllama(model=modele, temperature=0, num_predict=100).bind_tools(descriptions)
    return _llms[modele]


def _choisir(llm, messages) -> tuple[dict | None, dict]:
    """L'outil choisi (comme la case « comprendre » : un nom inconnu vaut « aucun »), et les jetons utilisés."""
    reponse = llm.invoke([SystemMessage(agent.SYSTEME), *agent.pour_le_llm(messages)])
    jetons = reponse.usage_metadata or {}
    appel = reponse.tool_calls[0] if reponse.tool_calls else None
    if appel is None or appel["name"] not in CONNUS:
        return None, jetons
    return {"outil": appel["name"], "arguments": appel.get("args") or {}}, jetons


def call_api(prompt: str, options: dict, context: dict) -> dict:
    modele = options.get("config", {})["modele"]
    variables = context["vars"]
    llm = _llm(modele)
    debut = time.perf_counter()
    messages = []
    for precedent in variables.get("avant") or []:
        messages.append(HumanMessage(precedent))
        choix, _ = _choisir(llm, messages)
        # Comme dire() dans agent.py : la réponse retient l'outil choisi, seul ce que le LLM relira.
        messages.append(AIMessage("…", additional_kwargs={"outil": choix["outil"]} if choix else {}))
    messages.append(HumanMessage(variables["question"]))
    choix, jetons = _choisir(llm, messages)
    return {
        "output": choix or {"outil": None, "arguments": {}},
        "latencyMs": round(1000 * (time.perf_counter() - debut)),
        "tokenUsage": {
            "prompt": jetons.get("input_tokens", 0),
            "completion": jetons.get("output_tokens", 0),
            "total": jetons.get("total_tokens", 0),
        },
    }
