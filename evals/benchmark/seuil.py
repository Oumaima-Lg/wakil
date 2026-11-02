"""Le seuil bloquant de la CI : la note du modèle de Wakil sur le paquet « test » ne doit pas descendre sous le seuil.

La note est celle du rapport (outil et paramètres justes, questions jamais vues). Le seuil est fixé à l'avance, d'après
la mesure de référence (qwen3:4b-instruct, 78 % sur Colab le 01/11/2026), moins une marge pour le bruit d'une autre
machine (le CPU du runner GitHub calcule un peu différemment d'un GPU) : il ne se règle pas après avoir vu un échec.

Lancer depuis evals/benchmark, après le benchmark : ../../apps/agent-api/.venv/bin/python seuil.py qwen3:4b-instruct
"""

import os
import sys

from rapport import lire

SEUIL = float(os.environ.get("BENCHMARK_SEUIL", "75"))  # en %


def note(reponses: list[dict]) -> tuple[int, int]:
    """(réussies, total) sur le paquet test."""
    test = [r for r in reponses if r["paquet"] == "test"]
    return sum(r["reussi"] for r in test), len(test)


def main(modele: str) -> int:
    reussies, total = note(lire().get(modele, []))
    if not total:
        print(f"Aucune réponse du paquet test pour {modele} : le benchmark n'a pas tourné.")
        return 1
    pourcent = 100 * reussies / total
    verdict = "réussi" if pourcent >= SEUIL else "ÉCHEC"
    print(f"{modele} : {reussies}/{total} = {pourcent:.1f} % (seuil {SEUIL:.0f} %) → {verdict}")
    return 0 if pourcent >= SEUIL else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
