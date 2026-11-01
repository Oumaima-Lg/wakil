-- Migration pour une base déjà créée (schema.sql n'est joué qu'à la création du volume) : le contenu est le même que
-- dans schema.sql. Appliquer une fois, depuis la racine du dépôt :
--   docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < apps/bank-api/migrations/001-idempotence.sql

-- Idempotence des opérations qui déplacent de l'argent (voir app/idempotence.py) : une clé par client, gardée 24 h
-- avec la réponse donnée.
CREATE TABLE IF NOT EXISTS idempotence (
    client_id  INTEGER NOT NULL REFERENCES clients (id),
    cle        TEXT NOT NULL,
    empreinte  TEXT NOT NULL,  -- SHA-256 de la route et du contenu de la demande
    reponse    JSONB,          -- rempli dans la même transaction que l'opération
    cree_le    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (client_id, cle)
);
