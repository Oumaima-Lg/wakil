# Image du site (Next.js), construite depuis apps/web :
#   docker build --build-arg AGENT_API_URL=http://agent-api:8001 --build-arg PORTAIL_API_URL=http://portail-api:8003 -t wakil/web .
#
# Les adresses d'agent-api et de portail-api sont figées au build : les règles de réécriture de next.config.ts
# (/api/chat → agent-api, le reste de /api → portail-api) sont calculées par « next build ». Une autre adresse, c'est
# une autre image.
#
# Trois étapes : les paquets npm, la construction, puis une image finale qui ne garde que le serveur « standalone »
# (le minimum produit par next build) et tourne avec l'utilisateur « node », sans droits.

ARG NODE=node:24-slim

FROM ${NODE} AS dependances
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

FROM ${NODE} AS construction
WORKDIR /app
ARG AGENT_API_URL
ARG PORTAIL_API_URL
ENV AGENT_API_URL=${AGENT_API_URL} PORTAIL_API_URL=${PORTAIL_API_URL} NEXT_TELEMETRY_DISABLED=1
COPY --from=dependances /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM ${NODE}
WORKDIR /app
ARG AGENT_API_URL
ARG PORTAIL_API_URL
# Les mêmes adresses à l'exécution : la page d'accueil interroge portail-api côté serveur (ListeClientsDemo).
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000 \
    AGENT_API_URL=${AGENT_API_URL} PORTAIL_API_URL=${PORTAIL_API_URL}
# Les correctifs de sécurité Debian (Trivy les signale), puis sans npm, npx ni corepack : le serveur n'a besoin que de
# node, et npm embarque ses propres copies de paquets (undici, brace-expansion…) qui ont elles aussi des failles.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
        /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack
COPY --from=construction --chown=node:node /app/.next/standalone ./
COPY --from=construction --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
