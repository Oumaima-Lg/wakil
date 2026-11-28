# Développer Wakil en local

> **Données 100 % fictives – projet de démonstration.** Ce document détaille une partie du [README](../README.md).

## Installation

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

Les mêmes services dans leurs **images de production** : un Dockerfile commun aux cinq services Python ([`apps/python.Dockerfile`](../apps/python.Dockerfile)) et celui du site ([`apps/web/Dockerfile`](../apps/web/Dockerfile)), construits en plusieurs étapes, lancés avec un utilisateur sans droits, sans `.env` ni outils de construction dans l'image. Seul le site est ouvert sur le PC (http://localhost:3100) ; les autres services ne se joignent qu'entre eux, et chacun ne reçoit que ses propres secrets. Les conteneurs utilisent l'Ollama du PC.

```bash
docker compose --profile images up -d --build
```

Pour les arrêter sans arrêter la base : `docker compose --profile images rm -sf web agent-api portail-api mcp-tools rag-faq bank-api`.

Les tests, et les contrats d'architecture (`lint-imports`) :

```bash
cd apps/bank-api && uv run --env-file ../../.env pytest      # base démarrée et remplie
cd apps/mcp-tools && uv run pytest && uv run lint-imports    # le test lance son serveur MCP ; banque simulée
cd apps/portail-api && uv run pytest && uv run lint-imports  # banque simulée, paire de clés de test
cd apps/rag-faq && uv run pytest && uv run lint-imports      # le test lance son serveur MCP ; sans Ollama ni base
cd apps/agent-api && uv run pytest && uv run lint-imports    # sans Ollama ni serveurs MCP (doublures)
cd apps/web && npm run lint && npm run typecheck
cd evals && ../apps/agent-api/.venv/bin/python -m pytest benchmark securite   # les juges du benchmark et des attaques
```

## Relancer les mesures

Le benchmark n'a besoin ni de la base de données ni d'aucun secret : seulement Ollama, les deux serveurs MCP (pour la liste des outils) et promptfoo. Un modèle à la fois ; la liste est dans [`promptfooconfig.yaml`](../evals/benchmark/promptfooconfig.yaml).

```bash
cd evals && npm ci && npm run benchmark   # sur le PC : Ollama, mcp-tools (8002) et rag-faq (8004) démarrés
```

Sur un GPU gratuit, avec le notebook [`evals/benchmark/colab.ipynb`](../evals/benchmark/colab.ipynb) : [ouvrir dans Google Colab](https://colab.research.google.com/github/Oumaima-Lg/wakil/blob/main/evals/benchmark/colab.ipynb), choisir le GPU T4, puis tout exécuter. Les résultats d'une machine ne se comparent qu'à ceux de la même machine.

La recherche dans la FAQ (base et Ollama démarrés, FAQ indexée), avec un autre modèle d'embeddings par `WAKIL_EMBEDDINGS` et sa consigne par `WAKIL_EMBEDDINGS_QUESTION` :

```bash
cd apps/rag-faq && uv run --env-file ../../.env python ../../evals/faq/mesurer.py
```

Les attaques (les six services démarrés, la carte de Salma active), le dernier mot étant le nom du passage :

```bash
cd apps/agent-api && uv run --env-file ../../.env python ../../evals/securite/attaquer.py avant
```

## Les captures d'écran du README

Un Chrome sans fenêtre (conteneur `navigateur`, profil `captures`) parcourt le site avec la cliente de démo Salma et refait les images de [`docs/captures/`](captures/). Il ne confirme aucune opération : la carte « Wach nconfirmi ? » est photographiée puis annulée.

```bash
docker compose --profile images --profile captures up -d --build
cd apps/agent-api && uv run python ../../docs/captures/capturer.py
```

## L'infrastructure Azure (Terraform)

Le code de l'infrastructure est dans [`infra/terraform/`](../infra/terraform/) : `bootstrap` (l'état Terraform et
l'alerte de budget) et `environnement` (la démo). Les choix sont expliqués dans
[l'ADR 0005](adr/0005-deploiement-azure.md). **Il n'a pas encore été appliqué** : pas de compte Azure pour l'instant.

Le vérifier sans compte, comme la CI, avec Terraform et Trivy dans leurs images (aucune installation) :

```bash
cd infra/terraform
TF="docker run --rm -u $(id -u):$(id -g) -e HOME=/tmp -v $PWD:/infra hashicorp/terraform:1.17.1"
$TF -chdir=/infra fmt -recursive -check
$TF -chdir=/infra/environnement init -backend=false && $TF -chdir=/infra/environnement validate
docker run --rm -v $PWD:/infra:ro aquasec/trivy:0.76.2 config /infra
```

Avec un compte (plus tard), dans cet ordre : `az login`, `export ARM_SUBSCRIPTION_ID=…`, puis le bootstrap
(`terraform.tfvars` copié de l'exemple, `terraform init && terraform apply`), puis l'environnement (`etat.tfbackend`
rempli avec les sorties du bootstrap, `terraform init -backend-config=etat.tfbackend`, `terraform plan`). Avant le
premier `apply` de l'environnement, il faudra l'image d'Ollama et le job d'initialisation de la base (ADR 0005).

## Intégration continue

À chaque pull request, [GitHub Actions](../.github/workflows/) vérifie :

- les **secrets** dans tout l'historique Git (gitleaks) et le **style** Python (ruff) ;
- les **tests** et les contrats d'architecture des cinq services Python, bank-api avec sa base et ses données fictives ;
- le **site** : lint, types et build ;
- l'**infrastructure** : `terraform fmt` et `validate` des deux modules, et les règles de sécurité de Trivy (`trivy config`, bloquant sur les écarts graves) ;
- les **six images** : construites comme en local, scannées par [Trivy](https://trivy.dev/) (bloquant si une faille grave a un correctif disponible), avec leur liste de composants (SBOM au format CycloneDX) jointe au passage ;
- le **benchmark bloquant** : `qwen3:4b-instruct` doit garder au moins 75 % d'outils et de paramètres justes sur les 113 questions du paquet test (79,6 % mesurés sur le CPU du runner, en 16 minutes). Il ne mesure que si l'agent, les outils, les questions, la FAQ ou le juge changent.

La branche `main` est protégée : toute modification passe par une pull request et ces vérifications. Les actions sont épinglées par leur SHA (un tag peut être déplacé vers du code malveillant, un SHA non), et Dependabot propose leurs mises à jour.
