"""Lance le benchmark modèle par modèle, puis écrit le rapport.

Un modèle à la fois : sur un PC de 8 Go, Ollama ne garde qu'un modèle en mémoire, et alterner les modèles à chaque
question les rechargerait sans cesse (3 questions en 4 minutes lors du premier essai).

Lancer depuis evals/ : npm run benchmark            (tous les modèles de promptfooconfig.yaml)
                       npm run benchmark -- qwen3   (seulement les modèles dont le nom contient « qwen3 »)
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ICI = Path(__file__).resolve().parent
PYTHON = ICI.parents[1] / "apps" / "agent-api" / ".venv" / "bin" / "python"
RESULTATS = ICI / "resultats"


def nom_de_fichier(modele: str) -> str:
    return re.sub(r"[^\w.-]", "_", modele)


def main(filtre: str = "") -> None:
    RESULTATS.mkdir(exist_ok=True)
    config = yaml.safe_load((ICI / "promptfooconfig.yaml").read_text())
    environnement = {**os.environ, "PROMPTFOO_PYTHON": str(PYTHON), "PROMPTFOO_DISABLE_TELEMETRY": "1"}
    for fournisseur in config["providers"]:
        modele = fournisseur["label"]
        if filtre not in modele:
            continue
        print(f"\n=== {modele}")
        commande = ["npx", "promptfoo", "eval", "-c", "promptfooconfig.yaml", "--no-progress-bar",
                    "--filter-providers", f"^{re.escape(modele)}$", "-o", str(RESULTATS / f"{nom_de_fichier(modele)}.json")]  # fmt: skip
        code = subprocess.run(commande, cwd=ICI, env=environnement).returncode
        if code not in (0, 100):  # 100 : l'évaluation s'est bien déroulée, mais des questions ont échoué
            sys.exit(code)
    subprocess.run([str(PYTHON), str(ICI / "rapport.py")], check=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
