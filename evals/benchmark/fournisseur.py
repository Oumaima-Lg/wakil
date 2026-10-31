"""Fournisseur promptfoo : l'étape 1 de Wakil (le LLM choisit l'outil et ses paramètres), par le vrai chemin de l'agent.

Le même prompt système, les mêmes outils (annoncés par les serveurs MCP, qui doivent tourner) et le même format
d'historique que la case « comprendre » d'agent-api. Aucun outil n'est exécuté : ni la banque ni la FAQ ne sont
appelées. Le modèle vient de la configuration du fournisseur (config: modele: …).

Pour une question de suite, les messages d'avant passent d'abord par le même LLM : l'historique contient alors les
outils qu'il a vraiment choisis, comme dans une conversation réelle.

Deux réglages par modèle (config du fournisseur) :
- raisonnement: false : coupe la réflexion d'un modèle qui « réfléchit » avant de répondre (qwen3:8b) ; sinon notre
  limite de 100 morceaux le couperait en pleine réflexion ;
- mode: json : pour un modèle sans appel d'outils natif (Atlas-Chat). Les outils sont décrits dans le prompt (mêmes
  descriptions), et Ollama impose seulement une réponse en JSON valide. Pas de schéma : pour le suivre, Ollama impose
  aux paramètres un ordre fixe (mesuré le 31/10 : après « beneficiaire », le « montant » devenait interdit), alors que
  les appels d'outils natifs ne sont pas contraints non plus. La liste fermée reste assurée par agent.choisir, qui
  ignore un nom d'outil inconnu. Ce mode n'existe pas encore dans agent-api : il sert à mesurer si un spécialiste de la
  darija comprend mieux les demandes.
"""

import json
import sys
import time
from functools import cache
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "apps" / "agent-api"))  # le code de l'agent, sans le copier

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402

from app import agent, outils  # noqa: E402

_llms: dict[tuple, object] = {}  # un LLM par réglage (modèle, mode, raisonnement), créé une fois par processus

CONSIGNE_JSON = (
    "Outils disponibles :\n{outils}\n\n"
    'Réponds seulement en JSON : {{"appels": [{{"outil": "nom de l\'outil", "arguments": {{...}}}}]}}. '
    "Un appel par demande du client ; une liste vide si aucun outil ne convient."
)


@cache  # une seule demande tools/list par processus : elle ne doit pas compter dans le temps de chaque question
def _descriptions() -> list[dict]:
    descriptions, _ = outils.descriptions_pour_le_llm({*agent.OUTILS, agent.OUTIL_FAQ}, set(agent.OPERATIONS))
    return descriptions


def outils_en_texte(descriptions: list[dict]) -> str:
    """Les mêmes descriptions que celles données aux modèles qui appellent des outils, écrites dans le prompt."""
    lignes = []
    for description in descriptions:
        fonction = description["function"]
        proprietes = fonction["parameters"]["properties"]
        parametres = ", ".join(
            f"{nom} ({p['description']})" if "description" in p else nom for nom, p in proprietes.items()
        )
        lignes.append(f"- {fonction['name']} : {fonction['description']} Paramètres : {parametres or 'aucun'}.")
    return "\n".join(lignes)


def historique_json(messages: list[AnyMessage]) -> list[AnyMessage]:
    """L'historique de pour_le_llm pour un modèle sans appel d'outils : chaque appel passé devient la réponse JSON que
    le modèle aurait écrite, et le message « Fait » disparaît (les tours client / modèle restent alternés)."""
    lus = []
    for message in agent.pour_le_llm(messages):
        if isinstance(message, HumanMessage):
            lus.append(message)
        elif isinstance(message, AIMessage):
            appels = [{"outil": appel["name"], "arguments": appel["args"]} for appel in message.tool_calls]
            lus.append(AIMessage(json.dumps({"appels": appels}, ensure_ascii=False)))
    return lus


def appels_du_json(texte: str) -> tuple[list[dict], bool]:
    """Les appels écrits par le modèle, au format des appels d'outils (name, args), et si le JSON était lisible."""
    try:
        appels = json.loads(texte)["appels"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return [], False  # coupé par la limite de longueur, par exemple : compté comme « aucun outil »
    return [{"name": a.get("outil", ""), "args": a.get("arguments") or {}} for a in appels if isinstance(a, dict)], True


def _llm(config: dict):
    cle = (config["modele"], config.get("mode"), config.get("raisonnement"))
    if cle not in _llms:
        descriptions = _descriptions()
        if config.get("mode") == "json":
            # 200 morceaux : le JSON écrit en entier est plus long qu'un appel d'outil natif
            _llms[cle] = ChatOllama(model=config["modele"], temperature=0, num_predict=200, format="json")
        else:
            _llms[cle] = ChatOllama(
                model=config["modele"], temperature=0, num_predict=100, reasoning=config.get("raisonnement")
            ).bind_tools(descriptions)
    return _llms[cle]


def _choisir(llm, messages, mode: str | None) -> tuple[dict, dict]:
    """Ce que Wakil fait des appels du LLM, avec les mêmes règles que la case « comprendre » (agent.choisir : un nom
    inconnu est ignoré, une opération passe seule, jusqu'à 3 lectures), et les jetons utilisés.

    outils : tous les outils que Wakil va appeler pour ce message (plusieurs lectures, ou un seul outil)."""
    if mode == "json":
        systeme = agent.SYSTEME + "\n\n" + CONSIGNE_JSON.format(outils=outils_en_texte(_descriptions()))
        reponse = llm.invoke([SystemMessage(systeme), *historique_json(messages)])
        appels, json_lisible = appels_du_json(reponse.content)
    else:
        reponse = llm.invoke([SystemMessage(agent.SYSTEME), *agent.pour_le_llm(messages)])
        appels, json_lisible = reponse.tool_calls, True
    choix = agent.choisir(appels)
    outils_appeles = [lecture["outil"] for lecture in choix["lectures"]] or ([choix["outil"]] if choix["outil"] else [])
    sortie = {"outil": choix["outil"], "arguments": choix["arguments"], "outils": outils_appeles}
    if not json_lisible:
        sortie["json_illisible"] = True
    return sortie, reponse.usage_metadata or {}


def call_api(prompt: str, options: dict, context: dict) -> dict:
    config = options.get("config", {})
    variables = context["vars"]
    llm = _llm(config)
    debut = time.perf_counter()
    messages = []
    for precedent in json.loads(variables.get("avant") or "[]"):  # en texte JSON (voir questions.en_texte)
        messages.append(HumanMessage(precedent))
        choix, _ = _choisir(llm, messages, config.get("mode"))
        # Comme dire() dans agent.py : chaque réponse retient l'outil choisi, seul ce que le LLM relira.
        messages += [AIMessage("…", additional_kwargs={"outil": outil}) for outil in choix["outils"]] or [
            AIMessage("…")
        ]
    messages.append(HumanMessage(variables["question"]))
    choix, jetons = _choisir(llm, messages, config.get("mode"))
    return {
        "output": choix,
        "latencyMs": round(1000 * (time.perf_counter() - debut)),
        "tokenUsage": {
            "prompt": jetons.get("input_tokens", 0),
            "completion": jetons.get("output_tokens", 0),
            "total": jetons.get("total_tokens", 0),
        },
    }
