"""Lecture d'un flux SSE dans les tests."""

import json


def evenements(reponse):
    """Découpe un flux SSE en liste de (nom de l'événement, données), en ignorant les commentaires comme un navigateur."""
    resultat = []
    for bloc in reponse.text.strip().split("\n\n"):
        if bloc.startswith(":"):
            continue  # « : battement »
        champs = dict(ligne.split(": ", 1) for ligne in bloc.splitlines())
        resultat.append((champs["event"], json.loads(champs["data"])))
    return resultat
