# /// script
# requires-python = ">=3.12"
# dependencies = ["faker", "psycopg[binary]"]
# ///
"""Remplit la Banque Atlas Démo avec des données 100 % fictives.

Lancer depuis la racine du dépôt : uv run --env-file .env data/seed/generer_donnees.py
Relancer le script efface tout et recrée les mêmes clients, comptes et montants (graine fixe).
"""

import os
import random
from datetime import datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

import psycopg
from faker import Faker

GRAINE = 2026  # même graine = mêmes données à chaque lancement
NB_CLIENTS = 200
NB_TRANSACTIONS = 20
MAROC = ZoneInfo("Africa/Casablanca")
CODE_BANQUE = "000"  # tous les RIB commencent par 000 : aucun ne peut ressembler à celui d'une vraie banque

# Prénoms et noms courants, mélangés au hasard : les combinaisons ne visent aucune personne réelle.
PRENOMS = [
    "Mohamed", "Youssef", "Amine", "Hamza", "Omar", "Mehdi", "Karim", "Anas", "Ayoub", "Ilyas",
    "Hicham", "Rachid", "Said", "Khalid", "Adil", "Fatima", "Khadija", "Salma", "Imane", "Sara",
    "Nadia", "Meryem", "Hajar", "Zineb", "Aicha", "Houda", "Laila", "Siham", "Asmae", "Ghita",
]
NOMS = [
    "Alaoui", "Benali", "Bennani", "Berrada", "Chraibi", "El Amrani", "El Idrissi", "Fassi", "Haddad",
    "Kettani", "Lahlou", "Mansouri", "Naciri", "Ouazzani", "Rami", "Saidi", "Tazi", "Zahraoui", "Bouzid",
    "Cherkaoui", "El Ouafi", "Hajji", "Jabri", "Lamrani", "Moussaoui", "Ziani", "Belhaj", "Ait Ali",
]
VILLES = [
    "Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir",
    "Meknès", "Oujda", "Kénitra", "Tétouan", "Salé", "El Jadida",
]

# Fournisseur : (montant minimum, montant maximum) en DH. Uniquement des noms « (démo) ».
FOURNISSEURS = {
    "Eau & Électricité (démo)": (80, 600),
    "Internet (démo)": (199, 499),
    "Mobile (démo)": (49, 299),
}
# Libellés génériques, sans aucune marque réelle.
DEPENSES = [
    ("Courses supermarché", 80, 900), ("Retrait guichet automatique", 100, 2000),
    ("Restaurant", 60, 450), ("Pharmacie", 30, 600), ("Taxi", 15, 120),
    ("Carburant", 150, 700), ("Café", 10, 60), ("Vêtements", 150, 1200),
]
ENTREES = [("Salaire (démo)", 4000, 15000), ("Virement reçu", 200, 3000)]

# Clients proposés sur l'écran de connexion, chacun avec un scénario à tester.
DEMO = [
    # Cas normal : l'exemple du README (solde 2 350 DH, facture d'eau 312 DH).
    {"prenom": "Salma", "nom": "Alaoui", "ville": "Casablanca", "solde": "2350.00", "plafond": "10000.00",
     "factures": [("Eau & Électricité (démo)", "312.00"), ("Internet (démo)", "249.00")]},
    # Solde insuffisant : sa facture Internet doit être refusée.
    {"prenom": "Youssef", "nom": "Berrada", "ville": "Rabat", "solde": "150.00", "plafond": "5000.00",
     "factures": [("Internet (démo)", "349.00")]},
    # Plafond bas : un virement de plus de 2 000 DH doit être refusé.
    {"prenom": "Nadia", "nom": "Tazi", "ville": "Marrakech", "solde": "18500.00", "plafond": "2000.00",
     "factures": [("Mobile (démo)", "99.00")]},
]

fake = Faker()
Faker.seed(GRAINE)
random.seed(GRAINE)


def montant(minimum, maximum):
    """Montant exact au centime : un Decimal, jamais un float."""
    return Decimal(random.randint(minimum * 100, maximum * 100)) / 100


def client_aleatoire():
    fournisseurs = random.sample(list(FOURNISSEURS), random.randint(1, 3))
    return {
        "prenom": random.choice(PRENOMS),
        "nom": random.choice(NOMS),
        "ville": random.choice(VILLES),
        "solde": montant(50, 25000),
        "plafond": Decimal(random.choice([5000, 10000, 20000])),
        "factures": [(f, montant(*FOURNISSEURS[f])) for f in fournisseurs],
    }


def creer_client(conn, c):
    """Crée le client, son compte, ses transactions et ses factures. Renvoie (client_id, nom complet, rib)."""
    client_id = conn.execute(
        "INSERT INTO clients (prenom, nom, ville) VALUES (%s, %s, %s) RETURNING id",
        (c["prenom"], c["nom"], c["ville"]),
    ).fetchone()[0]

    rib = CODE_BANQUE + fake.unique.numerify("#" * 21)
    compte_id = conn.execute(
        "INSERT INTO comptes (client_id, rib, solde, plafond_virement) VALUES (%s, %s, %s, %s) RETURNING id",
        (client_id, rib, c["solde"], c["plafond"]),
    ).fetchone()[0]

    transactions = []
    for _ in range(NB_TRANSACTIONS):
        if random.random() < 0.1:
            libelle, mini, maxi = random.choice(ENTREES)
            signe = 1
        else:
            libelle, mini, maxi = random.choice(DEPENSES)
            signe = -1
        # Un jour des 60 derniers (jamais aujourd'hui, pour éviter une heure dans le futur), entre 8 h et 22 h.
        jour = fake.date_between(start_date="-60d", end_date="-1d")
        date = datetime.combine(jour, time(random.randint(8, 21), random.randint(0, 59)), tzinfo=MAROC)
        transactions.append((compte_id, date, signe * montant(mini, maxi), libelle))
    # executemany envoie toutes les lignes d'un coup au lieu de faire un aller-retour par ligne.
    conn.cursor().executemany(
        "INSERT INTO transactions (compte_id, date, montant, libelle) VALUES (%s, %s, %s, %s)",
        transactions,
    )

    conn.cursor().executemany(
        "INSERT INTO factures (client_id, fournisseur, montant) VALUES (%s, %s, %s)",
        [(client_id, fournisseur, somme) for fournisseur, somme in c["factures"]],
    )
    # Une ancienne facture déjà payée, pour tester le refus d'un double paiement.
    ancienne = random.choice(list(FOURNISSEURS))
    conn.execute(
        "INSERT INTO factures (client_id, fournisseur, montant, statut) VALUES (%s, %s, %s, 'payee')",
        (client_id, ancienne, montant(*FOURNISSEURS[ancienne])),
    )
    return client_id, f"{c['prenom']} {c['nom']}", rib


with psycopg.connect(
    host="localhost",
    port=5432,
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    dbname=os.environ["POSTGRES_DB"],
) as conn:
    conn.execute("TRUNCATE clients, comptes, transactions, factures, beneficiaires, audit RESTART IDENTITY")

    clients = [creer_client(conn, c) for c in DEMO]
    clients += [creer_client(conn, client_aleatoire()) for _ in range(NB_CLIENTS - len(DEMO))]

    # Les bénéficiaires sont d'autres clients de la banque : les virements restent internes et fictifs.
    beneficiaires = []
    for client_id, _, _ in clients:
        autres = [c for c in clients if c[0] != client_id]
        for _, nom_complet, rib in random.sample(autres, random.randint(1, 3)):
            beneficiaires.append((client_id, nom_complet, rib))
    conn.cursor().executemany(
        "INSERT INTO beneficiaires (client_id, nom, rib) VALUES (%s, %s, %s)", beneficiaires
    )

    totaux = conn.execute(
        """SELECT (SELECT count(*) FROM clients), (SELECT count(*) FROM comptes),
                  (SELECT count(*) FROM transactions), (SELECT count(*) FROM factures),
                  (SELECT count(*) FROM beneficiaires)"""
    ).fetchone()

print("Clients : {}  ·  Comptes : {}  ·  Transactions : {}  ·  Factures : {}  ·  Bénéficiaires : {}".format(*totaux))
print("Clients de démo :", ", ".join(f"{nom} (id {cid})" for cid, nom, _ in clients[: len(DEMO)]))
