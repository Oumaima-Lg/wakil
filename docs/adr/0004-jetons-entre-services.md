# ADR 0004 — Prouver le client de service en service : relais du jeton de session, puis jeton court

- **Statut** : acceptée
- **Date** : 01/11/2026

## Contexte

Le navigateur prouve qui il est à `portail-api` et `agent-api` par un jeton de session signé en RS256 (ADR 0001).
Derrière, `mcp-tools` et `bank-api` croyaient l'en-tête `X-Client-Id`, posé par le service qui les appelait. Or
n'importe qui sur le réseau interne peut écrire cet en-tête. La mesure « avant » de S5
([`evals/securite/resultats.md`](../../evals/securite/resultats.md)) l'a confirmé : 4 attaques sur 29 réussissaient
ainsi (lire le solde de Youssef, préparer un virement depuis son compte, directement à la banque ou au serveur MCP).

## Décision

Chaque service prouve le client au suivant avec un jeton signé, que le suivant vérifie avec une clé publique :

```text
navigateur  ── cookie : jeton de session (portail-api, 30 min) ──────▶ agent-api
agent-api   ── le MÊME jeton, relayé (aud contient mcp-tools) ────────▶ mcp-tools
mcp-tools   ── NOUVEAU jeton de 60 s, signé par mcp-tools (aud bank-api) ─▶ bank-api
portail-api ── jeton de 60 s, signé par portail-api (aud bank-api) ──▶ bank-api
```

| Service | Clé privée (signe) | Clés publiques (vérifie) |
|---|---|---|
| portail-api | sessions et jetons courts | — |
| agent-api | **aucune** | portail-api |
| mcp-tools | jetons courts vers la banque | portail-api |
| bank-api | **aucune** | portail-api, mcp-tools |

- `agent-api` relaie le jeton par une variable de contexte du tour (`outils.JETON_DU_CLIENT`) : il n'est jamais écrit
  dans la mémoire PostgreSQL de l'agent. Avant de le relayer, `agent-api` vérifie qu'il est bien celui du client de la
  conversation.
- `bank-api` lit l'émetteur annoncé (`iss`) seulement pour choisir la clé, puis exige une signature de cette clé :
  se dire « mcp-tools » sans sa clé privée ne mène à rien.
- Chaque service refuse un jeton qui ne le nomme pas dans `aud`. Le jeton de session ne nomme pas `bank-api` : un
  cookie volé ne permet pas d'appeler la banque directement.

## Pourquoi

- **`agent-api` ne peut toujours fabriquer aucun client.** C'est le service qui contient le LLM, donc le plus exposé.
  S'il était piraté, il ne pourrait agir que pour les clients connectés à ce moment-là, et pas plus de 30 minutes.
- **C'est la règle de la spécification MCP** : un serveur MCP ne retransmet pas à l'API qui est derrière lui le jeton
  qu'il a reçu (« token passthrough »). `mcp-tools` signe donc son propre jeton, destiné à la seule banque.
- **Des jetons de 60 secondes vers la banque** : un jeton trouvé dans un journal ne sert presque à rien.

## Alternatives écartées

- **`agent-api` signe les jetons** (direction notée le 23/10/2026) : c'était plus simple, mais un `agent-api` piraté
  pourrait se faire passer pour n'importe quel client.
- **Relayer le jeton de session jusqu'à la banque** : une seule paire de clés suffirait, mais c'est le « token
  passthrough » interdit par la spécification MCP, et un jeton de 30 minutes circulerait jusqu'au cœur de la banque.
- **Seulement un réseau interne (S6)** : il le faut aussi, mais seul il ne protège pas d'un service voisin compromis.
  Les deux se complètent (défense en profondeur).

## Conséquences

- Une paire de clés de plus (`MCP_JWT_CLE_PRIVEE`, `MCP_JWT_CLE_PUBLIQUE`), générée par
  `uv run python -m app.jetons` dans `apps/mcp-tools`. En S6, chaque Container App ne recevra de Key Vault que ses clés.
- **Limite connue** : avec le jeton de session valide d'un client, un appel direct à `mcp-tools` peut joindre la
  confirmation dans `_meta` sans passer par la carte de Wakil. Cela ne donne pas plus de droits que le client
  lui-même dans son espace, mais la confirmation n'est pas encore prouvée cryptographiquement.
- Mesurée par les attaques `banque-…` et `mcp-…` du rapport de sécurité, dont trois visent les jetons eux-mêmes
  (jeton forgé, jeton de session volé).
