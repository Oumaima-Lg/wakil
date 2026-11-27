# Le benchmark darija

> **Données 100 % fictives – projet de démonstration.** Ce document détaille une partie du [README](../README.md).

Le cœur du projet : une évaluation ouverte qui mesure si un modèle d'IA **comprend une demande bancaire en darija et choisit le bon outil, avec les bons paramètres**. Des modèles darija existent, mais aucune évaluation publique ne mesure s'ils savent *agir*.

**Ce qui est mesuré.** L'étape 1 de Wakil, par son vrai chemin (même prompt, mêmes outils annoncés par les serveurs MCP, même historique de conversation), sans rien exécuter. Une réponse est réussie si le modèle choisit le bon outil, avec les paramètres attendus, **sans rien inventer** (un bénéficiaire ou un montant absent de la phrase fait échouer). Le juge est du code, pas un LLM : réussi ou raté, sans zone grise.

**Les questions** ([`data/benchmark/`](../data/benchmark/)). 113 questions jamais utilisées pour régler Wakil : 35 écrites à la main par l'auteure, avec ses fautes et ses abréviations, et 78 générées par une IA puis relues par elle. Elles couvrent la darija en lettres arabes, en lettres latines (arabizi) et mélangée au français, ainsi que le français, l'anglais et l'arabe standard. 57 autres questions, qui ont déjà servi à régler Wakil, sont mesurées à part : elles donneraient un score trop optimiste.

## Les modèles du LLM

Mesure du 01/11/2026 sur Google Colab (GPU NVIDIA T4), les trois modèles sur la même machine. Détail, échecs compris : [`evals/benchmark/resultats.md`](../evals/benchmark/resultats.md).

| Modèle (Ollama, local) | Outil et paramètres justes | Bon outil | Temps médian (GPU T4) | Taille |
|---|---|---|---|---|
| **`qwen3:4b-instruct`** (choisi pour la V1) | **78 %** (88/113) | 83 % | **0,4 s** | 2,5 Go |
| `atlas-chat:9b` (spécialiste darija, en mode JSON) | **81 %** (91/113) | 85 % | 1,6 s | 5,8 Go |
| `qwen3:8b` (raisonnement coupé) | 73 % (82/113) | 80 % | 0,7 s | 5,2 Go |

Au premier tour, sur le PC (90 questions), `llama3.2:3b` (58 %) et `atlas-chat:2b` (54 %) avaient été écartés.

| Langue (questions de test) | `qwen3:4b-instruct` | `atlas-chat:9b` | `qwen3:8b` |
|---|---|---|---|
| Darija, toutes écritures (78) | 73 % | **79 %** | 68 % |
| · en lettres arabes (21) | 71 % | **81 %** | 76 % |
| · en lettres latines (33) | 64 % | **76 %** | 58 % |
| · mélange darija-français (24) | **88 %** | 83 % | 75 % |
| Français (16) | 75 % | **81 %** | 75 % |
| Anglais (9) | **100 %** | 89 % | 89 % |
| Arabe standard (10) | **100 %** | 80 % | 90 % |

| Auteur des questions | `qwen3:4b-instruct` | `atlas-chat:9b` | `qwen3:8b` |
|---|---|---|---|
| Écrites à la main (35) | 66 % | **80 %** | 71 % |
| Générées par IA, relues (78) | **83 %** | 81 % | 73 % |

## Le modèle d'embeddings de la FAQ

Retrouver la bonne fiche de la FAQ, sur 38 questions de FAQ et 10 qui n'en sont pas ([`evals/faq/embeddings/`](../evals/faq/embeddings/)). « hit@1 » : la bonne fiche arrive en premier ; « hit@3 » : elle est parmi les trois premières. Qwen3-Embedding et embeddinggemma sont conçus pour recevoir une consigne avant le texte : ils sont mesurés sans, puis avec.

| Modèle | hit@1 | hit@3 | Darija en lettres arabes | Au meilleur seuil : bonne fiche / mauvaise fiche |
|---|---|---|---|---|
| **`bge-m3`** (choisi pour la V1) | **71 %** | 89 % | 60 % | **63 % / 11 %** |
| `qwen3-embedding:0.6b`, avec consigne | 68 % | **95 %** | 60 % | 63 % / 26 % |
| `embeddinggemma`, avec ses formats | **71 %** | 92 % | **70 %** | 47 % / 13 % |

## Ce que le benchmark a appris

1. **Les scores globaux ne départagent pas les trois modèles** (test de McNemar sur les questions où ils divergent : p ≥ 0,11). Le choix de la V1 s'est fait sur le reste : vitesse, taille, appel d'outils natif, licence, et un déploiement sans GPU. Le raisonnement complet : [docs/adr/0003-choix-des-modeles.md](adr/0003-choix-des-modeles.md).
2. **Les questions générées par une IA flattent le modèle généraliste** : `qwen3:4b-instruct` passe de 83 % sur les questions générées à 66 % sur les phrases écrites à la main. Le spécialiste darija tient à 80 % sur les deux.
3. **Chaque modèle est meilleur là où il a été entraîné** : Atlas-Chat en darija, qwen en anglais et en arabe standard.
4. **La génération d'un modèle compte plus que sa taille** : `qwen3:8b` (avril 2025) fait moins bien que `qwen3:4b-instruct` (juillet 2025, réentraîné pour suivre les consignes).
5. **Chaque outil ajouté peut voler des questions aux autres** : avec `lister_beneficiaires`, huit questions de FAQ (« zide liya benifciaire jdide ») partent vers la liste des bénéficiaires, pour qwen comme pour Atlas.
6. **Une mesure peut se tromper, et ses erreurs se publient aussi** : un schéma JSON imposé par Ollama interdisait le montant après le bénéficiaire (premier passage d'Atlas invalide) ; sans leur consigne, les modèles d'embeddings étaient sous-estimés (Qwen3-Embedding : 58 % au lieu de 68 %).

Les échecs restants sont publiés avec leurs familles dans [`resultats.md`](../evals/benchmark/resultats.md) et dans les conversations annotées ([`annotations.md`](../data/benchmark/annotations.md)) : bénéficiaires inventés par le LLM (« Ali » pour « liya ana »), « dibloque liya la carte » compris comme un blocage, questions de FAQ refusées.

## Relancer les mesures

Sur le PC ou sur un GPU gratuit (Google Colab) : voir [Relancer les mesures](developpement.md#relancer-les-mesures).
