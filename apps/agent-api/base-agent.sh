#!/bin/bash
# Base séparée de l'agent Wakil (ses conversations), avec son propre utilisateur.
# Moindre privilège : l'agent n'a aucun droit sur la base de la banque, il ne la lit qu'à travers bank-api.
#
# Lancé tout seul par PostgreSQL à la création du volume. Sur une base qui existe déjà, une seule fois :
#   docker compose exec -T db bash -s < apps/agent-api/base-agent.sh
# (le script est lu sur le disque : la copie montée dans le conteneur peut être une ancienne version, car un fichier
# monté seul reste lié à l'ancien fichier quand un éditeur le remplace)
# Le script peut être relancé sans risque : il ne crée que ce qui manque.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v agent="$AGENT_POSTGRES_USER" -v mdp="$AGENT_POSTGRES_PASSWORD" \
  -v base="$AGENT_POSTGRES_DB" -v banque="$POSTGRES_DB" <<'SQL'
-- \gexec exécute la requête que le SELECT a fabriquée : c'est la façon de faire « CREATE … IF NOT EXISTS » en psql.
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'agent', :'mdp')
  WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'agent') \gexec
SELECT format('CREATE DATABASE %I OWNER %I', :'base', :'agent')
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'base') \gexec

-- Par défaut, PostgreSQL laisse tout utilisateur se connecter à toute base (droit CONNECT donné à PUBLIC).
-- On ferme cette porte : l'agent ne peut même pas ouvrir une connexion vers la base de la banque.
SELECT format('REVOKE CONNECT ON DATABASE %I FROM PUBLIC', :'banque') \gexec
SELECT format('REVOKE CONNECT ON DATABASE %I FROM PUBLIC', :'base') \gexec
SQL
