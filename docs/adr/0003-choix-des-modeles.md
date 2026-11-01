# ADR 0003 — Les modèles de la version 1.0 : qwen3:4b-instruct pour comprendre, bge-m3 pour la FAQ

- **Statut** : acceptée
- **Date** : 01/11/2026

## Contexte

Wakil utilise deux modèles, tous deux locaux (Ollama) :

1. **un LLM**, qui lit la demande du client et choisit l'outil et ses paramètres (étape 1 : il ne rédige rien, ne
   calcule rien et ne voit jamais les données du compte) ;
2. **un modèle d'embeddings**, qui retrouve la fiche de la FAQ la plus proche de la question (service `rag-faq`).

Contraintes de la version 1.0 :

- **la darija d'abord**, en lettres arabes, en lettres latines (arabizi) et mélangée au français, mais aussi le
  français, l'anglais et l'arabe standard (vision multilingue) ;
- **des modèles locaux seulement** (décision du 30/10/2026) : une banque garde ses données chez elle ;
- **un déploiement sur Azure sans GPU**, dans les 100 USD d'Azure for Students (S6) ;
- **un choix appuyé sur des mesures**, pas sur des réputations.

## Décision

- **LLM : `qwen3:4b-instruct`**, seul, avec l'appel d'outils natif (déjà branché dans agent-api).
- **Embeddings : `bge-m3`**, déjà utilisé, avec le seuil de similarité de 0,60.

## Mesures

### Le LLM : benchmark darija ([`evals/benchmark/resultats.md`](../../evals/benchmark/resultats.md))

Une réponse est réussie si le LLM choisit le bon outil, avec les paramètres attendus, sans rien inventer (juge
déterministe, pas de juge LLM). 113 questions jamais vues pour régler Wakil, dont 35 écrites par Oumaima et 78
générées par une IA puis relues par elle. Mesure du 01/11/2026 sur Google Colab (GPU NVIDIA T4), les trois modèles
sur la même machine.

| Critère | qwen3:4b-instruct | atlas-chat:9b | qwen3:8b |
|---|---|---|---|
| Outil et paramètres justes (113 questions) | 78 % | 81 % | 73 % |
| Questions écrites par Oumaima (35) | 66 % | **80 %** | 71 % |
| Questions générées, relues (78) | **83 %** | 81 % | 73 % |
| Darija, toutes écritures (78) | 73 % | **79 %** | 68 % |
| · en lettres latines (33) | 64 % | **76 %** | 58 % |
| · en lettres arabes (21) | 71 % | **81 %** | 76 % |
| · mélange darija-français (24) | **88 %** | 83 % | 75 % |
| Français (16) | 75 % | **81 %** | 75 % |
| Anglais (9) | **100 %** | 89 % | 89 % |
| Arabe standard (10) | **100 %** | 80 % | 90 % |
| Hors sujet refusé (11, tous paquets) | 9/11 | 2/11 (envoyé à la FAQ, sans danger) | 10/11 |
| Temps médian, GPU T4 | **0,4 s** | 1,6 s | 0,7 s |
| Temps médian, PC de 8 Go (31/10) | **2,6 s** | 8,1 s | 7,3 s |
| Taille | **2,5 Go** | 5,8 Go | 5,2 Go |
| Appel d'outils | **natif** | mode JSON (sortie JSON demandée dans le prompt) | natif |
| Licence | **Apache 2.0** | conditions d'usage de Gemma | Apache 2.0 |

**Aucun écart global n'est démontré** : sur les questions où deux modèles ne sont pas d'accord, le test de McNemar
donne p = 0,69 (Atlas 9B contre qwen3:4b), 0,11 (Atlas 9B contre qwen3:8b) et 0,21 (qwen3:4b contre qwen3:8b). Une
première comparaison sur le PC (31/10, 90 questions, cinq modèles) avait déjà écarté `llama3.2:3b` (58 %) et
`atlas-chat:2b` (54 %).

### Les embeddings : recherche dans la FAQ ([`evals/faq/embeddings/`](../../evals/faq/embeddings/))

38 questions de FAQ et 10 qui n'en sont pas, toutes différentes des questions types écrites dans les fiches (pas de
fuite). Mesure du 01/11/2026 sur le PC, même index. Qwen3-Embedding et embeddinggemma sont conçus pour recevoir une
consigne avant le texte : ils ont été mesurés sans, puis avec (Qwen3-Embedding : « Instruct: Given a bank customer's
question, retrieve the FAQ entry that answers it\nQuery: … » avant la question ; embeddinggemma : « task: search
result | query: … » pour la question, « title: none | text: … » pour les fiches). Réglages `WAKIL_EMBEDDINGS_QUESTION`
et `WAKIL_EMBEDDINGS_FICHE` de rag-faq.

| Critère | bge-m3 | qwen3-embedding:0.6b | avec consigne | embeddinggemma | avec formats |
|---|---|---|---|---|---|
| La bonne fiche en premier (hit@1) | **71 %** | 58 % | 68 % | 68 % | **71 %** |
| Dans les trois premières (hit@3) | 89 % | 92 % | **95 %** | 92 % | 92 % |
| Darija en lettres arabes (hit@1, 10 questions) | 60 % | 30 % | 60 % | 50 % | **70 %** |
| Au meilleur seuil : bonne fiche citée / mauvaise fiche citée | **63 % / 11 %** (0,60) | 53 % / 26 % (0,60) | 63 % / 26 % (0,55) | 55 % / 24 % (0,60) | 47 % / 13 % (0,45) |
| Taille | 1,16 Go | 0,64 Go | 0,64 Go | **0,62 Go** | **0,62 Go** |

Chaque modèle a sa propre échelle de similarité : on les compare chacun à son meilleur seuil, pas au même nombre.

## Pourquoi ces choix

**qwen3:4b-instruct.** Les scores ne départagent pas les trois modèles : ce sont les autres critères qui décident, et
ils vont tous dans le même sens.

- Il est le seul qui tienne sur une petite machine Azure sans GPU, dans le budget de S6 : 2,5 Go, 0,4 s sur un GPU,
  2,6 s sur un PC de 8 Go.
- Il appelle les outils nativement et il est déjà branché : aucun risque nouveau pour la V1.
- Il refuse proprement le hors-sujet, et il est le meilleur en anglais et en arabe standard.
- Sa licence (Apache 2.0) est la plus simple pour livrer Wakil à d'autres banques.
- `qwen3:8b` n'est meilleur sur aucun critère : la génération du modèle (qwen3:4b-instruct, juillet 2025, réentraîné
  pour suivre les consignes) compte plus que sa taille (qwen3:8b, avril 2025, hybride, raisonnement coupé).

**bge-m3.** Wakil cite **une seule fiche**, et seulement si elle dépasse le seuil : il faut beaucoup de bonnes fiches
citées et très peu de mauvaises. bge-m3 a le meilleur compromis (63 % de bonnes, 11 % de mauvaises). Avec sa
consigne, Qwen3-Embedding progresse beaucoup (hit@1 de 58 % à 68 %, lettres arabes de 30 % à 60 %) et met la bonne
fiche dans les trois premières 95 fois sur 100, le meilleur score ; mais pour autant de bonnes fiches citées, il en
cite plus de deux fois plus de mauvaises (26 %). embeddinggemma avec ses formats est le meilleur en lettres arabes,
mais il cite beaucoup moins de bonnes fiches au même niveau d'erreur.

## Conséquences

- La V1 garde l'architecture actuelle : rien à changer dans agent-api ni dans rag-faq.
- **Le point faible est connu et publié** : sur les questions écrites par Oumaima, qwen3:4b réussit 66 %, contre 83 %
  sur les questions générées. Les questions générées par une IA ressemblent moins à de vrais clients ; elles flattent
  le modèle généraliste.
- **La darija en lettres arabes reste la plus difficile**, pour le LLM (71 %) comme pour la recherche (60 %).
- Le code continue de vérifier ce que le LLM remplit (règle « le LLM choisit, le code vérifie ») : quel que soit le
  modèle, les chiffres d'une carte absents du message sont retirés, et chaque opération passe par la confirmation.

## Ce qui ferait changer d'avis (version 2)

- **Atlas-Chat 9B**, le spécialiste de la darija, est la piste principale : il réussit 80 % des questions d'Oumaima
  contre 66 % pour qwen3:4b (7 réussites contre 2 là où ils divergent ; p = 0,18, pas encore démontré). Avec une
  centaine de vraies questions et un hébergement avec GPU, à mesurer : Atlas seul, ou Atlas pour la darija et qwen pour
  les autres langues (aiguillage selon la langue). Il faudra ajouter le mode JSON dans agent-api et relire la licence.
- **Le RAG complet** (le LLM lit les trois fiches les plus proches et rédige à partir de la bonne) : ce n'est plus la
  première fiche qui compte, mais la présence de la bonne parmi les trois. Qwen3-Embedding avec sa consigne (95 % dans
  les trois premières, contre 89 % pour bge-m3) deviendrait alors probablement le meilleur choix.
- **Plus de questions par langue** : 9 à 16 questions en français, en anglais et en arabe standard ne donnent que des
  tendances (une question y vaut 6 à 11 points). Il en faudrait une trentaine par langue.

## Alternatives écartées

- **Un modèle cloud** (Gemini, DeepSeek, OpenAI, Claude) : écarté le 30/10/2026, la vision de production étant locale.
  Il pourra servir de point de comparaison dans le benchmark, sans entrer dans le produit.
- **La cascade** (Atlas traduit la darija, qwen choisit l'outil) : Atlas comprend déjà la darija directement ; une
  cascade additionnerait les temps de deux modèles, qui ne tiennent pas ensemble sur 8 Go.
- **`llama3.2:3b` et `atlas-chat:2b`** : nettement derniers (58 % et 54 %), retirés des mesures le 31/10/2026.
