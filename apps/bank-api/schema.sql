-- Banque Atlas Démo : données 100 % fictives – projet de démonstration.
-- Exécuté une seule fois par PostgreSQL, à la création du volume (docker compose up).

-- Pas de téléphone : aucune fonctionnalité n'en a besoin (minimisation des données, loi 09-08).
CREATE TABLE clients (
    id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prenom  TEXT NOT NULL,
    nom     TEXT NOT NULL,
    ville   TEXT NOT NULL
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

-- PostgreSQL n'indexe pas les clés étrangères tout seul : chaque route cherche par client ou par compte.
CREATE INDEX ON comptes (client_id);
CREATE INDEX ON transactions (compte_id, date DESC);
CREATE INDEX ON factures (client_id);
CREATE INDEX ON beneficiaires (client_id);
CREATE INDEX ON audit (client_id);
