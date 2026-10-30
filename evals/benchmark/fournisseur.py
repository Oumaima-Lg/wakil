"""Fournisseur promptfoo : l'étape 1 de Wakil (le LLM choisit l'outil et ses paramètres), par le vrai chemin de l'agent.

Le même prompt système, les mêmes outils (annoncés par les serveurs MCP, qui doivent tourner) et le même format
d'historique que la case « comprendre » d'agent-api. Aucun outil n'est exécuté : ni la banque ni la FAQ ne sont
appelées. Le modèle vient de la configuration du fournisseur (config: modele: …).

Pour une question de suite, les messages d'avant passent d'abord par le même LLM : l'historique contient alors les
outils qu'il a vraiment choisis, comme dans une conversation réelle.
"""

import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "apps" / "agent-api"))  # le code de l'agent, sans le copier

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402

from app import agent, outils  # noqa: E402

_llms: dict[str, object] = {}  # un LLM par modèle, créé une fois par processus


def _llm(modele: str):
    if modele not in _llms:
        descriptions, _ = outils.descriptions_pour_le_llm({*agent.OUTILS, agent.OUTIL_FAQ}, set(agent.OPERATIONS))
        _llms[modele] = ChatOllama(model=modele, temperature=0, num_predict=100).bind_tools(descriptions)
    return _llms[modele]


def _choisir(llm, messages) -> tuple[dict, dict]:
    """Ce que Wakil fait des appels du LLM, avec les mêmes règles que la case « comprendre » (agent.choisir : un nom
    inconnu est ignoré, une opération passe seule, jusqu'à 3 lectures), et les jetons utilisés.

    outils : tous les outils que Wakil va appeler pour ce message (plusieurs lectures, ou un seul outil)."""
    reponse = llm.invoke([SystemMessage(agent.SYSTEME), *agent.pour_le_llm(messages)])
    choix = agent.choisir(reponse.tool_calls)
    outils_appeles = [lecture["outil"] for lecture in choix["lectures"]] or ([choix["outil"]] if choix["outil"] else [])
    return {"outil": choix["outil"], "arguments": choix["arguments"], "outils": outils_appeles}, (
        reponse.usage_metadata or {}
    )


def call_api(prompt: str, options: dict, context: dict) -> dict:
    modele = options.get("config", {})["modele"]
    variables = context["vars"]
    llm = _llm(modele)
    debut = time.perf_counter()
    messages = []
    for precedent in json.loads(variables.get("avant") or "[]"):  # en texte JSON (voir questions.en_texte)
        messages.append(HumanMessage(precedent))
        choix, _ = _choisir(llm, messages)
        # Comme dire() dans agent.py : chaque réponse retient l'outil choisi, seul ce que le LLM relira.
        messages += [AIMessage("…", additional_kwargs={"outil": outil}) for outil in choix["outils"]] or [
            AIMessage("…")
        ]
    messages.append(HumanMessage(variables["question"]))
    choix, jetons = _choisir(llm, messages)
    return {
        "output": choix,
        "latencyMs": round(1000 * (time.perf_counter() - debut)),
        "tokenUsage": {
            "prompt": jetons.get("input_tokens", 0),
            "completion": jetons.get("output_tokens", 0),
            "total": jetons.get("total_tokens", 0),
        },
    }
