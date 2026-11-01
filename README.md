# Wakil — agent bancaire en darija, évalué et sécurisé

> **Données 100 % fictives – projet de démonstration.** « Banque Atlas Démo » n'existe pas ; aucun client, compte ou fournisseur n'est réel.

**Wakil** (وكيل, « agent ») est un assistant bancaire qui **comprend la darija** (écriture arabe, lettres latines ou mélange avec le français) et **agit** : consulter un solde, payer une facture, faire un virement. Il demande toujours une **confirmation** avant une opération.

Le projet publie aussi un **benchmark ouvert** : il mesure si les modèles d'IA comprennent une demande en darija et appellent le bon outil avec les bons paramètres. À notre connaissance, aucune évaluation publique de ce type n'existe pour la darija.

```text
Client : Salam, chhal bqa f compte dyali ?
Wakil  : Solde dyalek howa 2 350 DH.
Client : Mzyan, khelless liya la facture dyal l'eau.
Wakil  : Facture Eau & Électricité (démo) : 312 DH. Wach nconfirmi l'paiement ? (Oui / Non)
Client : Oui
Wakil  : Tkhelssat ✅
```

## Architecture

```mermaid
flowchart LR
    nav(["Navigateur"]) --> web["<b>web</b><br/>Next.js · interface seulement"]
    web -- "/api/… (session, pages)" --> portail["<b>portail-api</b><br/>session · espace · bac à sable"]
    web -- "/api/chat" --> agent["<b>agent-api (LangGraph)</b><br/>aiguille, confirme, répond"]
    agent <--> llm["<b>LLM</b> · qwen3:4b-instruct<br/>Ollama · choisit l'outil"]
    agent -- MCP --> outils["<b>mcp-tools</b><br/>seule porte de l'IA vers la banque"]
    agent -- MCP --> faq["<b>rag-faq</b><br/>RAG de la FAQ · bge-m3 + pgvector"]
    portail -- HTTP --> banque["<b>bank-api</b><br/>données et toutes les règles métier"]
    outils -- HTTP --> banque

    classDef sansIA fill:#e3f4e1,stroke:#3d8b37,color:#1d3b1a
    classDef ia fill:#eee5fa,stroke:#7a4fc2,color:#2e1a52
    classDef modele fill:#faeeda,stroke:#854f0b,color:#633806
    classDef rag fill:#faece7,stroke:#993c1d,color:#712b13
    class portail sansIA
    class agent,outils ia
    class llm modele
    class faq rag
```

En vert, les pages et le bac à sable, sans IA. En violet, le chemin de l'IA. En jaune, le LLM, qui **décide** quel outil appeler. En orange, le RAG de la FAQ, qui **cherche**.

| Service | Port | Son rôle | Ce qu'il ne fait jamais |
|---|---|---|---|
| `web` (Next.js) | 3000 | Les pages et le chat. Envoie `/api/chat` à agent-api et le reste de `/api/…` à portail-api | Aucune règle métier, aucun appel à bank-api |
| `portail-api` (FastAPI) | 8003 | Ouvre la session (jeton signé avec la clé privée, dans un cookie HttpOnly) et sert les pages de l'espace bancaire ; plus tard, le bac à sable des visiteurs | Aucune IA : ni LLM, ni agent, ni outil MCP |
| `agent-api` (FastAPI, LangGraph) | 8001 | Wakil : le LLM comprend la demande et choisit l'outil ; LangGraph aiguille vers les outils de la banque ou la FAQ, demande « Wach nconfirmi ? » avant toute opération, et le code écrit la réponse | Ne crée aucune session (il n'a que la clé publique), n'appelle jamais bank-api directement, n'a aucun accès à l'index de la FAQ |
| `mcp-tools` (serveur MCP) | 8002 | Les outils de la banque pour l'IA : retrouve la facture ou le bénéficiaire ; sans la confirmation du client, fait seulement une vérification à blanc | Ne prend jamais le client dans les arguments du LLM (il vient de l'en-tête de la requête) |
| `rag-faq` (serveur MCP) | 8004 | Le RAG de la FAQ : l'outil `question_faq` retrouve la fiche la plus proche (bge-m3 + pgvector, dans sa propre base) ; l'indexation de `faq.yaml` | Ne rédige rien, ne parle ni à la banque ni au LLM de l'agent, ne reçoit pas l'identité du client |
| `bank-api` (FastAPI, PostgreSQL) | 8000 | Les données fictives et toutes les règles : solde suffisant, plafond, facture déjà payée, compte du bon client ; journal d'audit | Ne connaît ni l'IA, ni le navigateur |

Trois règles tiennent cette découpe :

- **L'IA n'atteint la banque et la FAQ que par MCP** : agent-api → mcp-tools → bank-api, et agent-api → rag-faq. Chaque outil n'est accepté que de son serveur. Des contrats [import-linter](https://import-linter.readthedocs.io/) (l'équivalent Python d'ArchUnit) le vérifient à chaque `uv run lint-imports` :
  - agent-api ne peut importer aucun client HTTP ;
  - portail-api ne peut importer aucune brique d'IA ;
  - rag-faq ne peut importer ni LangGraph ni client HTTP.
- **La session est créée à un seul endroit** : portail-api signe le jeton (RS256) avec sa clé privée. agent-api le vérifie avec la clé publique, sans pouvoir en fabriquer.
- **Les règles métier ne sont jamais confiées au LLM** : c'est bank-api qui accepte ou refuse une opération.

Chaque service a sa propre base PostgreSQL et son propre utilisateur, sans droit sur les autres : la banque (`banque_atlas_demo`), les conversations de l'agent (`wakil_agent`) et les vecteurs de la FAQ (`wakil_faq`). Un agent piégé ne peut donc pas modifier la FAQ. Le LLM et le modèle d'embeddings tournent en local avec Ollama. Le pourquoi de cette découpe est expliqué dans [docs/adr/0001-roles-des-services.md](docs/adr/0001-roles-des-services.md).

Deux schémas pour comprendre : [les 6 services, le LLM qui décide et le RAG de la FAQ](docs/schemas/architecture.png), et [le trajet d'une question de FAQ puis d'un paiement, entre le LLM, l'agent, la FAQ, le serveur MCP et la banque](docs/schemas/agent-mcp-sequence.png).

### La FAQ, citée sans rien inventer

Pour une question générale (frais, plafond, carte perdue, sécurité…), Wakil retrouve la fiche de la [FAQ](data/faq/faq.yaml) la plus proche et **cite son texte tel quel**, avec sa source. Le LLM ne rédige rien : il reconnaît seulement que c'est une question de FAQ, et agent-api appelle l'outil `question_faq` du serveur MCP `rag-faq` avec la phrase du client. Le choix est expliqué dans [docs/adr/0002-faq-reponses-citees.md](docs/adr/0002-faq-reponses-citees.md).

1. **Indexation**, à chaque modification de la FAQ : le modèle d'embeddings `bge-m3` transforme le texte de chaque fiche, et chacune de ses questions types en darija, en un vecteur de 1024 nombres. Ces vecteurs sont rangés avec pgvector dans la base de rag-faq.
2. **À chaque question** : la phrase du client devient un vecteur, et pgvector trouve la fiche la plus proche (similarité cosinus). Sous le seuil de 0,60, Wakil répond qu'il n'a pas trouvé, au lieu de citer un texte qui ne répond pas.

À venir :

- traces OpenTelemetry vers Phoenix ;
- déploiement sur Azure (Terraform, Ansible, Vault, GitHub Actions).

## Stack

| Couche | Outils |
|---|---|
| Front-end | Next.js, TypeScript |
| Back-end | Python, FastAPI |
| IA | LangGraph, LangChain, MCP, Ollama, pgvector |
| Évaluation et sécurité | promptfoo, DeepEval, OWASP Top 10 LLM et agentique |
| Données | PostgreSQL, Faker |
| CI/CD | GitHub Actions, gitleaks, Trivy, Checkov |
| Infrastructure | Terraform, Ansible, HashiCorp Vault, Azure Key Vault |
| Cloud | Azure Container Apps, ACR, PostgreSQL Flexible Server |
| Observabilité | OpenTelemetry, Phoenix |

## Lancer en local

Prérequis : [Docker](https://docs.docker.com/get-docker/), [uv](https://docs.astral.sh/uv/) (Python), Node.js 24 et [Ollama](https://ollama.com).

```bash
# 1. Les secrets : copier le modèle, puis remplacer chaque « a-remplacer » par une valeur tirée au hasard,
#    par exemple : python3 -c "import secrets; print(secrets.token_urlsafe(32))"
cp .env.example .env

# 2. Les clés des jetons (RS256), ajoutées à la fin de .env (jamais commitées) : celles des sessions (portail-api),
#    puis celles des jetons courts de mcp-tools vers bank-api (voir docs/adr/0004-jetons-entre-services.md)
(cd apps/portail-api && uv run python -m app.cles >> ../../.env)
(cd apps/mcp-tools && uv run python -m app.jetons >> ../../.env)

# 3. Les modèles (langue : environ 2,5 Go ; embeddings : environ 1,2 Go), la base de données, les données fictives,
#    l'index de la FAQ et les paquets du site
ollama pull qwen3:4b-instruct
ollama pull bge-m3
docker compose up -d --wait
uv run --env-file .env data/seed/generer_donnees.py
(cd apps/rag-faq && uv run --env-file ../../.env python -m app.faq)
(cd apps/web && npm ci)
```

Sur un volume PostgreSQL créé avant le service rag-faq (29/10/2026), créer d'abord la base de la FAQ, une seule fois. `set -a` exporte les variables de `.env`, que `-e` transmet au conteneur sans les afficher :

```bash
set -a; . ./.env; set +a
```

```bash
docker compose exec -T -e FAQ_POSTGRES_USER -e FAQ_POSTGRES_PASSWORD -e FAQ_POSTGRES_DB db bash -s < apps/rag-faq/base-faq.sh
```

Puis lancer les six services d'une seule commande. [honcho](https://honcho.readthedocs.io/) lit le fichier `Procfile` (une ligne par service), affiche les journaux de chacun avec un préfixe de couleur, et Ctrl+C arrête tout :

```bash
uvx honcho start
```

Pour lancer un seul service, par exemple pour le redémarrer à part, copier sa ligne du `Procfile` dans un terminal.

Sur http://localhost:3000, choisir un client de démo, ouvrir l'espace bancaire, puis Wakil. Après quelques minutes sans message, Ollama décharge les modèles : la réponse suivante peut prendre jusqu'à 30 secondes. Sur un PC de 8 Go de mémoire, Ollama peut aussi décharger le LLM pour charger `bge-m3`, et inversement : la première question de FAQ peut alors prendre plus d'une minute.

Les tests, et les contrats d'architecture (`lint-imports`) :

```bash
cd apps/bank-api && uv run --env-file ../../.env pytest      # base démarrée et remplie
cd apps/mcp-tools && uv run pytest && uv run lint-imports    # le test lance son serveur MCP ; banque simulée
cd apps/portail-api && uv run pytest && uv run lint-imports  # banque simulée, paire de clés de test
cd apps/rag-faq && uv run pytest && uv run lint-imports      # le test lance son serveur MCP ; sans Ollama ni base
cd apps/agent-api && uv run pytest && uv run lint-imports    # sans Ollama ni serveurs MCP (doublures)
cd apps/web && npm run lint && npm run typecheck
```

Pour relancer les mesures du benchmark et de la FAQ : voir [Relancer les mesures](#relancer-les-mesures).

## Le benchmark darija

Le cœur du projet : une évaluation ouverte qui mesure si un modèle d'IA **comprend une demande bancaire en darija et choisit le bon outil, avec les bons paramètres**. Des modèles darija existent, mais aucune évaluation publique ne mesure s'ils savent *agir*.

**Ce qui est mesuré.** L'étape 1 de Wakil, par son vrai chemin (même prompt, mêmes outils annoncés par les serveurs MCP, même historique de conversation), sans rien exécuter. Une réponse est réussie si le modèle choisit le bon outil, avec les paramètres attendus, **sans rien inventer** (un bénéficiaire ou un montant absent de la phrase fait échouer). Le juge est du code, pas un LLM : réussi ou raté, sans zone grise.

**Les questions** ([`data/benchmark/`](data/benchmark/)). 113 questions jamais utilisées pour régler Wakil : 35 écrites à la main par l'auteure, avec ses fautes et ses abréviations, et 78 générées par une IA puis relues par elle. Elles couvrent la darija en lettres arabes, en lettres latines (arabizi) et mélangée au français, ainsi que le français, l'anglais et l'arabe standard. 57 autres questions, qui ont déjà servi à régler Wakil, sont mesurées à part : elles donneraient un score trop optimiste.

### Les modèles du LLM

Mesure du 01/11/2026 sur Google Colab (GPU NVIDIA T4), les trois modèles sur la même machine. Détail, échecs compris : [`evals/benchmark/resultats.md`](evals/benchmark/resultats.md).

| Modèle (Ollama, local) | Outil et paramètres justes | Bon outil | Temps médian (GPU T4) | Taille |
|---|---|---|---|---|
| **`qwen3:4b-instruct`** (choisi pour la V1) | **78 %** (88/113) | 83 % | **0,4 s** | 2,5 Go |
| `atlas-chat:9b` (spécialiste darija, en mode JSON) | **81 %** (91/113) | 85 % | 1,6 s | 5,8 Go |
| `qwen3:8b` (raisonnement coupé) | 73 % (82/113) | 80 % | 0,7 s | 5,2 Go |

Au premier tour, sur le PC (90 questions), `llama3.2:3b` (58 %) et `atlas-chat:2b` (54 %) avaient été écartés.

| Langue (questions de test) | `qwen3:4b-instruct` | `atlas-chat:9b` | `qwen3:8b` |
|---|---|---|---|
| Darija, toutes écritures (78) | 73 % | **79 %** | 68 % |
| · en lettres arabes (21) | 71 % | **81 %** | 76 % |
| · en lettres latines (33) | 64 % | **76 %** | 58 % |
| · mélange darija-français (24) | **88 %** | 83 % | 75 % |
| Français (16) | 75 % | **81 %** | 75 % |
| Anglais (9) | **100 %** | 89 % | 89 % |
| Arabe standard (10) | **100 %** | 80 % | 90 % |

| Auteur des questions | `qwen3:4b-instruct` | `atlas-chat:9b` | `qwen3:8b` |
|---|---|---|---|
| Écrites à la main (35) | 66 % | **80 %** | 71 % |
| Générées par IA, relues (78) | **83 %** | 81 % | 73 % |

### Le modèle d'embeddings de la FAQ

Retrouver la bonne fiche de la FAQ, sur 38 questions de FAQ et 10 qui n'en sont pas ([`evals/faq/embeddings/`](evals/faq/embeddings/)). « hit@1 » : la bonne fiche arrive en premier ; « hit@3 » : elle est parmi les trois premières. Qwen3-Embedding et embeddinggemma sont conçus pour recevoir une consigne avant le texte : ils sont mesurés sans, puis avec.

| Modèle | hit@1 | hit@3 | Darija en lettres arabes | Au meilleur seuil : bonne fiche / mauvaise fiche |
|---|---|---|---|---|
| **`bge-m3`** (choisi pour la V1) | **71 %** | 89 % | 60 % | **63 % / 11 %** |
| `qwen3-embedding:0.6b`, avec consigne | 68 % | **95 %** | 60 % | 63 % / 26 % |
| `embeddinggemma`, avec ses formats | **71 %** | 92 % | **70 %** | 47 % / 13 % |

### Ce que le benchmark a appris

1. **Les scores globaux ne départagent pas les trois modèles** (test de McNemar sur les questions où ils divergent : p ≥ 0,11). Le choix de la V1 s'est fait sur le reste : vitesse, taille, appel d'outils natif, licence, et un déploiement sans GPU. Le raisonnement complet : [docs/adr/0003-choix-des-modeles.md](docs/adr/0003-choix-des-modeles.md).
2. **Les questions générées par une IA flattent le modèle généraliste** : `qwen3:4b-instruct` passe de 83 % sur les questions générées à 66 % sur les phrases écrites à la main. Le spécialiste darija tient à 80 % sur les deux.
3. **Chaque modèle est meilleur là où il a été entraîné** : Atlas-Chat en darija, qwen en anglais et en arabe standard.
4. **La génération d'un modèle compte plus que sa taille** : `qwen3:8b` (avril 2025) fait moins bien que `qwen3:4b-instruct` (juillet 2025, réentraîné pour suivre les consignes).
5. **Chaque outil ajouté peut voler des questions aux autres** : avec `lister_beneficiaires`, huit questions de FAQ (« zide liya benifciaire jdide ») partent vers la liste des bénéficiaires, pour qwen comme pour Atlas.
6. **Une mesure peut se tromper, et ses erreurs se publient aussi** : un schéma JSON imposé par Ollama interdisait le montant après le bénéficiaire (premier passage d'Atlas invalide) ; sans leur consigne, les modèles d'embeddings étaient sous-estimés (Qwen3-Embedding : 58 % au lieu de 68 %).

Les échecs restants sont publiés avec leurs familles dans [`resultats.md`](evals/benchmark/resultats.md) et dans les conversations annotées ([`annotations.md`](data/benchmark/annotations.md)) : bénéficiaires inventés par le LLM (« Ali » pour « liya ana »), « dibloque liya la carte » compris comme un blocage, questions de FAQ refusées.

### Relancer les mesures

Le benchmark n'a besoin ni de la base de données ni d'aucun secret : seulement Ollama, les deux serveurs MCP (pour la liste des outils) et promptfoo. Un modèle à la fois ; la liste est dans [`promptfooconfig.yaml`](evals/benchmark/promptfooconfig.yaml).

```bash
cd evals && npm ci && npm run benchmark   # sur le PC : Ollama, mcp-tools (8002) et rag-faq (8004) démarrés
```

Sur un GPU gratuit, avec le notebook [`evals/benchmark/colab.ipynb`](evals/benchmark/colab.ipynb) : [ouvrir dans Google Colab](https://colab.research.google.com/github/Oumaima-Lg/wakil/blob/main/evals/benchmark/colab.ipynb), choisir le GPU T4, puis tout exécuter. Les résultats d'une machine ne se comparent qu'à ceux de la même machine.

La recherche dans la FAQ (base et Ollama démarrés, FAQ indexée), avec un autre modèle d'embeddings par `WAKIL_EMBEDDINGS` et sa consigne par `WAKIL_EMBEDDINGS_QUESTION` :

```bash
cd apps/rag-faq && uv run --env-file ../../.env python ../../evals/faq/mesurer.py
```

À venir avec S5 : le taux de réussite des attaques (injection de prompt, accès au compte d'un autre client…) avant et après chaque protection, et le benchmark bloquant dans la CI.

## Avancement

- [x] S0 — Premiers appels d'outils avec Ollama
- [x] S1 — Banque fictive (API + fausses données)
- [x] S2 — Agent LangGraph + interface Next.js (espace bancaire, chat en direct, version mobile)
- [x] S3 — Confirmation avant chaque opération, serveurs MCP (banque, FAQ), RAG sur la FAQ avec réponses citées
- [x] S4 — Benchmark darija : 5 modèles locaux comparés sur 113 questions, modèles de la V1 choisis (ADR 0003)
- [ ] S5 — Sécurité + CI avec évaluation bloquante
- [ ] S6 — Déploiement Azure avec Terraform
- [ ] S7 — Ansible, Vault, observabilité, budget
- [ ] S8 — Documentation, vidéo, version 1.0

## Auteure

Oumaima Laghjibi — Ingénieure logicielle · [LinkedIn](https://www.linkedin.com/in/oumaima-laghjibi-745786287) · [GitHub](https://github.com/Oumaima-Lg)

---

**English summary.** Wakil is a Darija-speaking banking agent built on a fully fictional bank. It understands Moroccan Arabic written in Arabic script, Latin script (Arabizi) or mixed with French, calls banking tools through MCP, and always asks for confirmation before any operation. The project publishes an open benchmark of LLM tool-calling accuracy in Darija (5 local models, 113 requests in Darija, French, English and Modern Standard Arabic; qwen3:4b-instruct chosen for v1, the Darija specialist Atlas-Chat 9B ahead on human-written requests), a security report on prompt-injection resistance, and is deployed on Azure with Terraform, Ansible, Vault and GitHub Actions.
