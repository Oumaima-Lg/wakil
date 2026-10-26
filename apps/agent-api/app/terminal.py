"""Discuter avec Wakil dans le terminal (bank-api et Ollama doivent tourner).

Lancer (depuis apps/agent-api) : uv run python -m app.terminal 1     (1 = Salma, 2 = Youssef, 3 = Nadia)
Les conversations restent en mémoire vive : elles disparaissent à la fermeture du terminal.
"""

import sys
import uuid

from app.agent import config, prochaine_entree, wakil

client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
conversation = config(client_id, str(uuid.uuid4()))  # une nouvelle conversation, avec mémoire, à chaque lancement
print(f"Wakil · Banque Atlas Démo · client {client_id} · Données 100 % fictives. Tape « q » pour quitter.")

while True:
    demande = input("\nToi   : ").strip()
    if demande == "q":
        break
    if not demande:
        continue
    etat = wakil.invoke(prochaine_entree(wakil, demande, client_id, conversation), conversation)
    en_attente = wakil.get_state(conversation).interrupts  # une opération attend « oui » ou « la »
    print(f"Wakil : {en_attente[0].value['texte'] if en_attente else etat['reponse']}")
    print(f"        (outil choisi : {etat['outil'] or '—'})")
