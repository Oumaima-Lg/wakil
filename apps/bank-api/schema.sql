-- Banque Atlas Démo : données 100 % fictives – projet de démonstration.
-- Exécuté une seule fois par PostgreSQL, à la création du volume (docker compose up).

-- Pas de téléphone : aucune fonctionnalité n'en a besoin (minimisation des données, loi 09-08).
-- La civilité a trois usages : l'illustration de la carte, « Bonjour Madame », l'accord de la darija (khellsi / khelless).
CREATE TABLE clients (
    id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    civilite  TEXT NOT NULL CHECK (civilite IN ('madame', 'monsieur')),
    prenom    TEXT NOT NULL,
    nom       TEXT NOT NULL,
    ville     TEXT NOT NULL
);

CREATE TABLE comptes (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id         INTEGER NOT NULL REFERENCES clients (id),
    rib               CHAR(24) NOT NULL UNIQUE CHECK (rib ~ '^[0-9]{24}$'),
    solde             NUMERIC(12, 2) NOT NULL CHECK (solde >= 0),
    plafond_virement  NUMERIC(12, 2) NOT NULL CHECK (plafond_virement > 0)
);

CREATE TABLE transactions (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    compte_id  INTEGER NOT NULL REFERENCES comptes (id),
    date       TIMESTAMPTZ NOT NULL DEFAULT now(),
    montant    NUMERIC(12, 2) NOT NULL CHECK (montant <> 0),  -- négatif : sortie d'argent, positif : entrée
    libelle    TEXT NOT NULL
);

CREATE TABLE factures (
    id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id    INTEGER NOT NULL REFERENCES clients (id),
    fournisseur  TEXT NOT NULL CHECK (fournisseur IN ('Eau & Électricité (démo)', 'Internet (démo)', 'Mobile (démo)')),
    montant      NUMERIC(12, 2) NOT NULL CHECK (montant > 0),
    statut       TEXT NOT NULL DEFAULT 'impayee' CHECK (statut IN ('payee', 'impayee'))
);

CREATE TABLE beneficiaires (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id  INTEGER NOT NULL REFERENCES clients (id),
    nom        TEXT NOT NULL,
    rib        CHAR(24) NOT NULL CHECK (rib ~ '^[0-9]{24}$'),
    UNIQUE (client_id, rib)
);

CREATE TABLE audit (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id     INTEGER NOT NULL REFERENCES clients (id),
    action        TEXT NOT NULL,
    details       JSONB NOT NULL,
    confirmee_le  TIMESTAMPTZ NOT NULL DEFAULT now()
);

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

-- PostgreSQL n'indexe pas les clés étrangères tout seul : chaque route cherche par client ou par compte.
CREATE INDEX ON comptes (client_id);
CREATE INDEX ON transactions (compte_id, date DESC);
CREATE INDEX ON factures (client_id);
CREATE INDEX ON beneficiaires (client_id);
CREATE INDEX ON audit (client_id);
