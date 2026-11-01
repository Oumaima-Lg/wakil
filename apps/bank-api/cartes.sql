-- Une carte fictive par compte, sans hasard : numéro masqué et expiration tirés de l'id du client.
-- Utilisé par data/seed/generer_donnees.py et par migrations/002-cartes.sql (même requête).
INSERT INTO cartes (client_id, compte_id, numero_masque, expiration)
SELECT c.client_id, c.id, '•••• ' || lpad(((c.client_id * 7919) % 10000)::text, 4, '0'),
       lpad((c.client_id % 12 + 1)::text, 2, '0') || '/' || (28 + c.client_id % 4)
FROM comptes c
WHERE NOT EXISTS (SELECT 1 FROM cartes k WHERE k.compte_id = c.id)
ORDER BY c.id;
