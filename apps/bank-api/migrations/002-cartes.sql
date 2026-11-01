-- Migration pour une base déjà créée : la table des cartes (comme dans schema.sql), puis une carte fictive par
-- compte (comme le script de données). Appliquer une fois, depuis la racine du dépôt :
--   docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < apps/bank-api/migrations/002-cartes.sql

-- Cartes bancaires, 100 % fictives : jamais de numéro complet ni de code, seulement « •••• 4821 ».
-- États : active ⇄ bloquee (temporaire), puis opposee (perte ou vol, définitif). Voir app/routers/cartes.py.
CREATE TABLE IF NOT EXISTS cartes (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id         INTEGER NOT NULL REFERENCES clients (id),
    compte_id         INTEGER NOT NULL REFERENCES comptes (id),
    numero_masque     TEXT NOT NULL CHECK (numero_masque ~ '^•••• [0-9]{4}$'),
    expiration        CHAR(5) NOT NULL CHECK (expiration ~ '^(0[1-9]|1[0-2])/[0-9]{2}$'),
    statut            TEXT NOT NULL DEFAULT 'active' CHECK (statut IN ('active', 'bloquee', 'opposee')),
    motif_opposition  TEXT CHECK (motif_opposition IN ('perte', 'vol')),
    remplacee_par     INTEGER REFERENCES cartes (id),  -- la nouvelle carte, après une opposition
    modifiee_le       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((statut = 'opposee') = (motif_opposition IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS cartes_client_id_idx ON cartes (client_id);

INSERT INTO cartes (client_id, compte_id, numero_masque, expiration)
SELECT c.client_id, c.id, '•••• ' || lpad(((c.client_id * 7919) % 10000)::text, 4, '0'),
       lpad((c.client_id % 12 + 1)::text, 2, '0') || '/' || (28 + c.client_id % 4)
FROM comptes c
WHERE NOT EXISTS (SELECT 1 FROM cartes k WHERE k.compte_id = c.id)
ORDER BY c.id;
