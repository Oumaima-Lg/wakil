# Image d'un service Python de Wakil : le même Dockerfile pour les cinq (bank-api, mcp-tools, portail-api, agent-api,
# rag-faq), le service en paramètre. Construire depuis la racine du dépôt, par exemple :
#   docker build -f apps/python.Dockerfile --build-arg SERVICE=bank-api -t wakil/bank-api .
# (docker compose --profile images le fait pour les six images, voir docker-compose.yml.)
#
# Deux étapes. La première installe les paquets avec uv, exactement ceux de uv.lock. L'image finale ne garde que
# Python, l'environnement virtuel et le code : ni uv, ni compilateur, ni fichier de construction. Elle tourne avec un
# utilisateur sans droits, et la structure du dépôt y est reproduite (/srv/apps/<service>, /srv/data/faq), car rag-faq
# retrouve la FAQ par son chemin relatif.

ARG PYTHON=python:3.14-slim

FROM astral/uv:0.13.0 AS uv

FROM ${PYTHON} AS construction
ARG SERVICE
COPY --from=uv /uv /usr/local/bin/uv
# Bytecode compilé d'avance (démarrage plus rapide), paquets copiés et non liés (l'environnement change d'étape),
# jamais de Python téléchargé par uv : celui de l'image sert.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/srv/.venv
WORKDIR /srv/apps/${SERVICE}
# Les dépendances d'abord, sans le code : cette couche reste en cache tant que uv.lock ne change pas.
COPY apps/${SERVICE}/pyproject.toml apps/${SERVICE}/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project
COPY apps/${SERVICE}/app ./app

# L'image d'un service. APPLICATION : l'objet ASGI que lance uvicorn (app.serveur:app pour les serveurs MCP).
FROM ${PYTHON} AS service
ARG SERVICE
ARG APPLICATION=app.main:app
ARG PORT=8000
# Les correctifs de sécurité Debian publiés depuis la construction de l'image de base (Trivy les signale), puis sans pip :
# l'application ne s'en sert jamais (uv a tout installé à l'étape d'avant), et pip embarque ses propres copies de
# paquets (urllib3, msgpack…) qui ont elles aussi des failles.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
    && python -m pip uninstall --yes --quiet pip \
    && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin wakil
COPY --from=construction /srv /srv
WORKDIR /srv/apps/${SERVICE}
ENV PATH=/srv/.venv/bin:$PATH PYTHONUNBUFFERED=1 APPLICATION=${APPLICATION} PORT=${PORT}
USER wakil
EXPOSE ${PORT}
CMD ["sh", "-c", "exec uvicorn \"$APPLICATION\" --host 0.0.0.0 --port \"$PORT\""]

# rag-faq a besoin de la FAQ (data/faq/faq.yaml) pour l'indexer ; les autres services ne la reçoivent pas.
FROM service AS rag-faq
COPY data/faq /srv/data/faq
