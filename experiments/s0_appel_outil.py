"""S0 : le modèle choisit-il le bon outil quand on lui parle en darija ?

Usage : python3 experiments/s0_appel_outil.py llama3.2:3b
Aucune bibliothèque à installer : on parle à Ollama en HTTP avec du JSON.
"""

import json
import sys
import time
import urllib.request

MODELE = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b-instruct"
# Ollama imite l'API d'OpenAI : le même JSON marchera plus tard avec Azure OpenAI.
URL = "http://localhost:11434/v1/chat/completions"

SYSTEME = (
    "Tu es Wakil, l'assistant de la Banque Atlas Démo (banque fictive). "
    "Le client écrit en darija marocaine, en lettres arabes ou latines, souvent mélangée au français. "
    "Si la demande concerne son compte, appelle l'outil adapté. Sinon, répondre en darija que tu ne t'occupes que de la banque."
)


def outil(nom, description):
    """Décrit un outil au format attendu par le modèle (ici sans paramètre)."""
    return {
        "type": "function",
        "function": {
            "name": nom,
            "description": description,
            "parameters": {"type": "object", "properties": {}},
        },
    }


OUTILS = [
    outil("consulter_solde", "Donne le solde actuel du compte du client."),
    outil("lister_transactions", "Liste les dernières opérations du compte du client : l'argent qui est sorti (dépenses, paiements) ou entré (virements reçus)."),
    outil("lister_factures", "Liste les factures impayées du client (eau, électricité, internet, mobile)."),
]

# (écriture, demande, outil attendu). None : aucun outil ne doit être appelé.
TESTS = [
    ("latin", "chhal bqa f compte dyali ?", "consulter_solde"),
    ("arabe", "شحال بقا فالحساب ديالي؟", "consulter_solde"),
    ("mélange", "bghit nchouf le solde dyali", "consulter_solde"),
    ("latin", "warini chno khrej mn compte dyali had simana", "lister_transactions"),
    ("latin", "donner moi ce qu'il a sorti de mon compte cette semaine", "lister_transactions"),
    ("arabe", "شنو هوما آخر العمليات اللي درت؟", "lister_transactions"),
    ("mélange", "3tini la liste dyal les transactions dyali", "lister_transactions"),
    ("latin", "fin mchaw flousi had chhar ?", "lister_transactions"),
    ("arabe", "واش دخلو ليا شي فلوس؟", "lister_transactions"),
    ("latin", "wach 3ndi chi fatora ma khlsthach ?", "lister_factures"),
    ("arabe", "واش عندي شي فاتورة ما خلصتهاش؟", "lister_factures"),
    ("mélange", "bghit n3ref les factures li mazal ma khlsthomch", "lister_factures"),
    ("latin", "kifach ndir tajine b l7em ?", None),
    ("arabe", "شكون ربح الماتش البارح؟", None),
    ("mélange", "chno la météo lyoum f Casa ?", None),
    ("mélange", "3awni nkteb CV dyali", None),
    ("mélange", "fin kayna a9rab pharmacie ?", None),
    ("francais", "je veux savoir ce qu'il me reste dans mon argent jusqu'à maintenant", "consulter_solde"),
]


def demander(demande):
    """Envoie une demande au modèle et renvoie son message de réponse."""
    corps = {
        "model": MODELE,
        "temperature": 0,  # toujours la même réponse pour la même demande
        "max_tokens": 200,  # coupe le modèle s'il part en boucle
        "tools": OUTILS,
        "messages": [
            {"role": "system", "content": SYSTEME},
            {"role": "user", "content": demande},
        ],
    }
    requete = urllib.request.Request(
        URL, data=json.dumps(corps).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(requete, timeout=600) as reponse:
        return json.load(reponse)["choices"][0]["message"]


demander("salam")  # charge le modèle en mémoire avant de chronométrer (~35 s la première fois)

reussis = {ecriture: 0 for ecriture, _, _ in TESTS}  # une case par écriture présente dans TESTS
for ecriture, demande, attendu in TESTS:
    debut = time.perf_counter()
    message = demander(demande)
    duree = time.perf_counter() - debut

    appels = message.get("tool_calls")  # absent quand le modèle répond par du texte
    choisi = appels[0]["function"]["name"] if appels else None
    if choisi == attendu:
        reussis[ecriture] += 1
    print(f"{'✅' if choisi == attendu else '❌'} {duree:5.1f} s  {demande}  →  {choisi}  (attendu : {attendu})")

print(f"\n{MODELE} : {sum(reussis.values())}/{len(TESTS)} bons choix")
for ecriture, n in reussis.items():
    total = sum(1 for e, _, _ in TESTS if e == ecriture)
    print(f"  {ecriture} : {n}/{total}")
