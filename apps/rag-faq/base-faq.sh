#!/bin/bash
# Base de la FAQ (vecteurs des fiches), avec son propre utilisateur : elle n'appartient qu'au service rag-faq.
# L'agent n'y a aucun accès : même piégé, il ne peut ni lire l'index autrement que par l'outil MCP, ni le modifier.
#
# Lancé tout seul par PostgreSQL à la création du volume. Sur une base qui existe déjà, une seule fois (depuis la racine
# du dépôt ; set -a exporte les variables de .env, que -e transmet au conteneur sans les afficher) :
#   set -a; . ./.env; set +a
#   docker compose exec -T -e FAQ_POSTGRES_USER -e FAQ_POSTGRES_PASSWORD -e FAQ_POSTGRES_DB db bash -s < apps/rag-faq/base-faq.sh
# Le script peut être relancé sans risque : il ne crée que ce qui manque.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v faq="$FAQ_POSTGRES_USER" -v mdp="$FAQ_POSTGRES_PASSWORD" -v base="$FAQ_POSTGRES_DB" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'faq', :'mdp')
  WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'faq') \gexec
SELECT format('CREATE DATABASE %I OWNER %I', :'base', :'faq')
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'base') \gexec
-- Comme pour les autres bases : personne d'autre ne peut s'y connecter.
SELECT format('REVOKE CONNECT ON DATABASE %I FROM PUBLIC', :'base') \gexec
SQL

# pgvector : activer une extension demande le superutilisateur.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$FAQ_POSTGRES_DB" \
  -c "CREATE EXTENSION IF NOT EXISTS vector"
