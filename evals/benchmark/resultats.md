# Benchmark darija de Wakil : résultats mesurés

Généré le 30/10/2026 par `evals/benchmark/rapport.py`, à partir de promptfoo. Données 100 % fictives.

**Ce qui est mesuré** : l'étape 1 de Wakil, par le vrai chemin de l'agent (même prompt, mêmes outils MCP, même historique). Une réponse est réussie si le LLM choisit le bon outil, avec les paramètres attendus, sans rien inventer. Aucun outil n'est exécuté.

**Les questions** : 10 jamais vues (paquet « test », qui donne la note) et 52 déjà utilisées pour régler Wakil (paquet « mise au point », score optimiste, donné à part).

## Classement

| Modèle | Bon outil (test) | Outil et paramètres justes (test) | Mise au point (outil et paramètres) | Temps médian | Temps p95 | Jetons par question |
|---|---|---|---|---|---|---|
| `llama3.2:3b` | 80 % (8/10) | **80 % (8/10)** | 50 % (26/52) | 0.6 s | 1.1 s | 980 |
| `qwen3:4b-instruct` | 80 % (8/10) | **80 % (8/10)** | 48 % (25/52) | 2.9 s | 12.6 s | 1088 |

## Par écriture (tous paquets)

| Modèle | arabe | latin | melange | francais |
|---|---|---|---|---|
| `llama3.2:3b` | 38 % (5/13) | 59 % (16/27) | 58 % (11/19) | 67 % (2/3) |
| `qwen3:4b-instruct` | 38 % (5/13) | 59 % (16/27) | 58 % (11/19) | 33 % (1/3) |

## Par catégorie (tous paquets)

| Modèle | factures | faq | floue | hors_sujet | non_disponible | operations | paiement | plafond | solde | suite | virement |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `llama3.2:3b` | 100 % (2/2) | 50 % (20/40) | 0 % (0/1) | 0 % (0/6) | 100 % (1/1) | 100 % (3/3) | 67 % (2/3) | 100 % (1/1) | 100 % (2/2) | 100 % (1/1) | 100 % (2/2) |
| `qwen3:4b-instruct` | 100 % (2/2) | 40 % (16/40) | 0 % (0/1) | 100 % (6/6) | 0 % (0/1) | 100 % (3/3) | 0 % (0/3) | 100 % (1/1) | 100 % (2/2) | 100 % (1/1) | 100 % (2/2) |

## Échecs du paquet test

| Modèle | Question | Écriture | Catégorie | Pourquoi |
|---|---|---|---|---|
| `llama3.2:3b` | bghit ndir virement | latin | floue | outil question_faq au lieu de faire_virement |
| `llama3.2:3b` | chkoun rbe7 l'match dyal lbare7 ? | latin | hors_sujet | outil question_faq au lieu de None |
| `qwen3:4b-instruct` | khelless liya l'internet | melange | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'internet' |
| `qwen3:4b-instruct` | bghit ndir virement | latin | floue | outil None au lieu de faire_virement |
