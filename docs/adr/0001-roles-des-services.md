# ADR 0001 — Des services découpés aux frontières de sécurité

- **Statut** : acceptée (complétée le 29/10/2026 : le RAG de la FAQ devient un sixième service, `rag-faq`, voir l'ADR 0002)
- **Date** : 26/10/2026

## Contexte

Jusqu'ici, `agent-api` faisait deux métiers : l'agent Wakil (le chat) et le portail de la banque (ouvrir la session, servir les pages de l'espace). Il avait donc son propre client de `bank-api`, en plus de celui du serveur MCP. Cela posait trois problèmes :

1. **Deux chemins vers la banque**, avec du code en double (deux fichiers `banque.py`).
2. **Le service le plus exposé gardait le plus de pouvoir.** `agent-api` reçoit les messages des clients et les donne à un LLM, donc il est la cible des injections de prompt. C'est pourtant lui qui détenait la clé qui crée les sessions, et un accès direct à la banque.
3. **Le bac à sable prévu après S8** (un visiteur crée et modifie son propre client fictif) ajoutera du CRUD sans IA, qui n'a rien à faire dans le service de l'agent.

Ce qui guide la découpe :

- le modèle « backend for frontend » ([Sam Newman](https://samnewman.io/patterns/architectural/bff/)) : un backend taillé pour son interface, avec les règles métier en aval ;
- dans MCP, l'hôte et l'agent pilotent le déroulé, et le serveur porte les capacités, la validation et le contrôle d'accès ;
- un agent qui lit du contenu non fiable doit avoir le moins de droits possible ([« lethal trifecta »](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)) ;
- commencer par un monolithe modulaire, et ne découper qu'aux frontières de sécurité.

## Décision

| Service | Rôle | Ce qu'il ne fait jamais |
|---|---|---|
| `web` (Next.js) | L'interface. Aiguille `/api/chat` vers `agent-api`, le reste de `/api/…` vers `portail-api` | Aucune règle métier, aucun appel à `bank-api` |
| `portail-api` | La session et les pages de l'espace ; plus tard, le bac à sable | Aucune IA (ni LLM, ni agent, ni MCP) |
| `agent-api` (LangGraph) | Wakil : le LLM choisit l'outil, le graphe aiguille vers la banque ou la FAQ, demande la confirmation, répond | Ne crée aucune session ; n'appelle jamais `bank-api` directement ; n'a aucun accès à l'index de la FAQ |
| `mcp-tools` | La seule porte de l'IA vers la banque | Ne prend jamais le client dans les arguments du LLM |
| `rag-faq` | Le RAG de la FAQ, en serveur MCP : retrouve la fiche qui répond, dans sa propre base | Ne rédige rien, ne parle pas à la banque, ne reçoit pas l'identité du client |
| `bank-api` | Les données et toutes les règles métier | Ne connaît ni l'IA, ni le navigateur |

**Sessions en RS256.** `portail-api` signe le jeton avec la clé privée. `agent-api` le vérifie avec la clé publique et ne peut donc pas en fabriquer. Le jeton nomme son émetteur (`iss: portail-api`) et ses destinataires (`aud: [portail-api, agent-api]`). Chaque service refuse un jeton qui ne le nomme pas.

**Ces règles sont vérifiées par le code.** Des contrats [import-linter](https://import-linter.readthedocs.io/) (l'équivalent Python d'ArchUnit) les contrôlent :

- `agent-api` ne peut importer aucun client HTTP ;
- `portail-api` ne peut importer aucune brique d'IA ;
- dans `mcp-tools`, le déroulé des outils (`operations.py`) ne dépend pas de MCP.

## Conséquences

- Un seul chemin de l'IA vers la banque : `agent-api` → `mcp-tools` → `bank-api`. Le rapport de sécurité (S5) n'a qu'une porte à attaquer et à mesurer.
- Si `agent-api` était compromis, l'attaquant ne pourrait ni créer de session pour un autre client, ni appeler la banque sans passer par les outils et leur confirmation.
- Un service de plus à lancer en local : un `Procfile` et la commande `uvx honcho start` lancent les six. En S6, ce sera aussi une Container App de plus, en `minReplicas=0`, donc sans coût quand elle ne sert pas.
- La vérification du jeton est écrite deux fois (une vingtaine de lignes dans `portail-api` et `agent-api`). C'est accepté plutôt que de créer une bibliothèque partagée.
- **Limites connues** :
  - En local, les deux clés sont dans le même `.env`. La vraie séparation viendra en S6 : chaque Container App ne recevra de Key Vault que la clé dont elle a besoin.
  - `bank-api` croit encore l'en-tête `X-Client-Id`. En S5, il vérifiera un jeton court et signé ; en S6, il ne sera joignable que de l'intérieur.

## Alternatives écartées

- **Garder le portail dans `agent-api`** : c'est le plus simple, mais le service le plus exposé garderait la clé des sessions et un accès direct à la banque.
- **Servir les pages par `mcp-tools`** : MCP sert à donner des outils à une IA, pas à servir des pages. Mélanger les deux brouillerait la seule frontière entre l'IA et la banque.
- **HS256 avec un secret partagé** : tout service qui vérifie les jetons pourrait aussi en fabriquer.
- **Le navigateur appelle `bank-api` directement** : la banque serait exposée, et n'importe qui pourrait écrire l'en-tête `X-Client-Id` d'un autre client.
