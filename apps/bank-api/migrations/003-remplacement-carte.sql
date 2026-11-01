-- Migration pour une base déjà créée : le lien d'une carte en opposition vers sa remplaçante (comme dans
-- schema.sql). Appliquer une fois, depuis la racine du dépôt :
--   docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < apps/bank-api/migrations/003-remplacement-carte.sql

ALTER TABLE cartes ADD COLUMN IF NOT EXISTS remplacee_par INTEGER REFERENCES cartes (id);
