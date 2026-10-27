# ADR 0002 — FAQ : retrouver la fiche par embeddings, et la citer sans la réécrire

- **Statut** : acceptée
- **Date** : 27/10/2026

## Contexte

Les clients posent aussi des questions générales : frais, plafond de virement, carte perdue, sécurité des codes. Avant cette décision, Wakil répondait par un refus, faute d'outil pour ces questions.

Trois difficultés :

1. **La darija n'a pas d'orthographe** : « virement », « الفيرمون », « sifet », « 7awel »… Une recherche par mots-clés échoue.
2. **Une banque ne doit jamais donner un tarif faux.** Le LLM local (`qwen3:4b-instruct`) écrit mal la darija et peut inventer un chiffre s'il rédige la réponse.
3. **La qualité doit se mesurer**, idéalement sans juge LLM.

## Décision

- **Les fiches** sont dans [`data/faq/faq.yaml`](../../data/faq/faq.yaml) : 13 fiches en français, qui disent exactement ce que fait bank-api (aucun frais, plafond par virement, pas de découvert…). Chacune porte de 5 à 9 questions types en darija (lettres arabes, latines, mélange) qui servent de pont vers le texte français.
- **La recherche se fait par embeddings**, avec `bge-m3` (multilingue, local dans Ollama, 1024 nombres par phrase). Les vecteurs sont rangés dans la base de l'agent avec pgvector ; une fiche prend le score de la plus proche de ses phrases.
- **La réponse est le texte de la fiche, cité tel quel.** Seule l'introduction est en darija. Le LLM ne fait que reconnaître une question de FAQ (outil `question_faq`, sans paramètre). On cherche avec **la phrase du client**, jamais avec une reformulation du LLM.
- **Seuil : similarité cosinus de 0,60.** En dessous, Wakil répond « ma l9itch jawab f la FAQ ».
- **La FAQ vit dans agent-api** : c'est la connaissance de l'agent, pas une donnée de client. mcp-tools reste la seule porte vers les données de la banque.

## Mesures (27/10/2026)

### Étape 2 : retrouver la fiche ([`evals/faq/resultats.md`](../../evals/faq/resultats.md))

Première mesure, sur 30 questions de test différentes des questions types des fiches : hit@1 67 %, hit@3 87 %.

Ensuite, 8 vraies questions d'Oumaima ont été ajoutées aux questions de test, et 8 questions types aux fiches « Ce que Wakil sait faire » et « Bénéficiaires ». Résultats sur les 38 questions :

| | hit@1 | hit@3 |
|---|---|---|
| Lettres arabes | 60 % | 80 % |
| Lettres latines | 71 % | 93 % |
| Mélange | 73 % | 91 % |
| Français | 100 % | 100 % |
| **Total** | **71 %** | **89 %** |

Ces nouvelles questions types ont été écrites **après** avoir vu les échecs : la hausse sur les questions d'Oumaima est donc optimiste. Le benchmark (S4) utilisera des questions jamais vues.

Choix du seuil :

| Seuil | FAQ bien servie | FAQ mal servie (mauvaise fiche citée) | FAQ sans réponse |
|---|---|---|---|
| 0,55 | 68 % | 21 % | 11 % |
| **0,60** | **63 %** | **11 %** | **26 %** |
| 0,65 | 42 % | 3 % | 55 % |

0,60 sert le plus de questions en gardant les mauvaises citations à 11 %. Le seuil seul ne sépare pas bien les questions hors sujet : leur meilleur score monte jusqu'à 0,63. **Le premier filtre est donc le LLM**, qui décide si c'est une question de FAQ.

Temps de recherche : médiane 59 ms quand `bge-m3` est déjà chargé.

### Étape 1 : le LLM envoie-t-il la question à la FAQ ? ([`evals/faq/routage.md`](../../evals/faq/routage.md))

Le premier essai d'Oumaima a révélé deux défauts, corrigés puis mesurés sur les 48 questions :

1. **Bug du prompt système** : écrit avant la FAQ, il ordonnait « si la demande concerne son compte, appelle l'outil adapté […] **sinon, réponds que tu ne t'occupes que de la banque** ». Il dit maintenant quand appeler `question_faq`. Le rapport d'avant est gardé dans [`routage-avant-correction.md`](../../evals/faq/routage-avant-correction.md).
2. **Les refus dans l'historique** : un petit modèle qui vient de refuser refuse encore. « comment ajouter un Bénéficiaire ? » allait à la FAQ seule, mais au refus après deux refus. Les refus restent affichés dans le chat, mais le LLM ne les lit plus.

| Choix de l'outil | Avant | Après |
|---|---|---|
| Questions de FAQ → `question_faq` | 26 % (lettres arabes 0 %) | **53 %** (lettres arabes 20 %) |
| Demandes sur le compte → leur outil | 80 % | 80 % |
| Hors sujet → aucun outil | 80 % | 100 % |

## Conséquences

- Wakil ne peut citer qu'un texte écrit et relu à l'avance : jamais un tarif inventé.
- La qualité se mesure de façon déterministe (hit@1, hit@3), sans juge LLM. Les questions de test serviront au benchmark (S4).
- Une règle de la banque qui change oblige à changer la fiche, puis à relancer l'indexation (`python -m app.faq`).
- **Limites mesurées** :
  - **Le maillon faible est le LLM** : même après correction, `qwen3:4b-instruct` n'envoie que 53 % des questions de FAQ à la FAQ, et 20 % en lettres arabes. C'est la comparaison de modèles du benchmark (S4).
  - Près de 3 questions sur 10 n'obtiennent pas la bonne fiche en premier.
  - En lettres latines, `bge-m3` réagit parfois plus aux mots d'une autre question type qu'au sens : « ch7al l7ed dyal l virement l wa7ed ? » obtient « Délai d'un virement » avec 0,86.
  - Sur un PC de 8 Go, Ollama alterne entre le LLM et `bge-m3` : la première question de FAQ peut prendre plus d'une minute.

## Alternatives écartées (pour l'instant)

- **Réponse rédigée par le LLM** (RAG classique) : plus naturelle, mais le risque d'un chiffre inventé et le besoin d'un juge LLM l'emportent. C'est une variante à mesurer au benchmark.
- **Recherche par mots-clés** (`LIKE`, plein texte) seule : inadaptée à la darija sans orthographe. Une recherche hybride (vecteurs + plein texte) reste une piste si les lettres latines restent faibles.
- **Fiches en darija** : plus proches du client, mais sans orthographe standard et plus longues à écrire et relire.
- **Index HNSW** : inutile pour 79 vecteurs, que PostgreSQL compare tous en une fraction de milliseconde.
