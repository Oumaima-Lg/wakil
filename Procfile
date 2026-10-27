# Les 5 services en une commande, depuis la racine du dépôt : uvx honcho start
# Avant : la base (docker compose up -d --wait) et Ollama démarrés, .env rempli (voir le README).
# honcho donne une variable PORT à chaque service : chaque ligne fixe donc son port elle-même.
bank: cd apps/bank-api && uv run --env-file ../../.env fastapi dev --port 8000
mcp: cd apps/mcp-tools && uv run --env-file ../../.env uvicorn app.serveur:app --port 8002 --reload
portail: cd apps/portail-api && uv run --env-file ../../.env fastapi dev --port 8003
agent: cd apps/agent-api && uv run --env-file ../../.env fastapi dev --port 8001
web: cd apps/web && npm run dev -- --port 3000
