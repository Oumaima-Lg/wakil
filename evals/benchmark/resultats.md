# Benchmark darija de Wakil : résultats mesurés

Généré le 30/10/2026 par `evals/benchmark/rapport.py`, à partir de promptfoo. Données 100 % fictives.

**Ce qui est mesuré** : l'étape 1 de Wakil, par le vrai chemin de l'agent (même prompt, mêmes outils MCP, même historique). Une réponse est réussie si le LLM choisit le bon outil, avec les paramètres attendus, sans rien inventer. Aucun outil n'est exécuté.

**Les questions** : 75 jamais vues (paquet « test », qui donne la note) et 52 déjà utilisées pour régler Wakil (paquet « mise au point », score optimiste, donné à part).

## Classement

| Modèle | Bon outil (test) | Outil et paramètres justes (test) | Mise au point (outil et paramètres) | Temps médian | Temps p95 | Jetons par question |
|---|---|---|---|---|---|---|
| `llama3.2:3b` | 71 % (53/75) | **56 % (42/75)** | 56 % (29/52) | 0.7 s | 2.3 s | 1313 |
| `qwen3:4b-instruct` | 81 % (61/75) | **79 % (59/75)** | 50 % (26/52) | 2.3 s | 9.1 s | 1451 |

## Par écriture (tous paquets)

| Modèle | arabe | latin | melange | francais |
|---|---|---|---|---|
| `llama3.2:3b` | 48 % (16/33) | 52 % (25/48) | 61 % (22/36) | 80 % (8/10) |
| `qwen3:4b-instruct` | 58 % (19/33) | 62 % (30/48) | 78 % (28/36) | 80 % (8/10) |

## Par catégorie (tous paquets)

| Modèle | beneficiaires | depenses | factures | faq | floue | hors_sujet | non_disponible | operations | paiement | plafond | plusieurs | solde | suite | virement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `llama3.2:3b` | 75 % (3/4) | 33 % (2/6) | 100 % (6/6) | 57 % (26/46) | 0 % (0/4) | 0 % (0/9) | 33 % (1/3) | 62 % (5/8) | 92 % (12/13) | 67 % (2/3) | 20 % (1/5) | 50 % (3/6) | 50 % (2/4) | 80 % (8/10) |
| `qwen3:4b-instruct` | 100 % (4/4) | 83 % (5/6) | 100 % (6/6) | 54 % (25/46) | 0 % (0/4) | 78 % (7/9) | 67 % (2/3) | 75 % (6/8) | 54 % (7/13) | 100 % (3/3) | 100 % (5/5) | 100 % (6/6) | 50 % (2/4) | 70 % (7/10) |

## Échecs du paquet test

| Modèle | Question | Écriture | Catégorie | Pourquoi |
|---|---|---|---|---|
| `llama3.2:3b` | شحال عندي فالكونط؟ | arabe | solde | outil question_faq au lieu de consulter_solde |
| `llama3.2:3b` | chhal fih l compte dyali daba | latin | solde | outil analyser_depenses au lieu de consulter_solde ; categorie inventé : 'null' |
| `llama3.2:3b` | شحال هو البلافون ديال الكونط ديالي؟ | arabe | plafond | outil analyser_depenses au lieu de consulter_plafond ; categorie inventé : 'null' |
| `llama3.2:3b` | achno drt b lflous f had l'ayam ? | latin | operations | outil analyser_depenses au lieu de lister_transactions ; categorie inventé : 'chhal srefti' |
| `llama3.2:3b` | affichili les dernières dépenses dyali | melange | operations | outil analyser_depenses au lieu de lister_transactions ; categorie inventé : 'dyali' |
| `llama3.2:3b` | شنو خلصت هاد الأيام؟ | arabe | operations | outil analyser_depenses au lieu de lister_transactions ; categorie inventé : 'null' |
| `llama3.2:3b` | dir liya paiement dyal facture lma | latin | paiement | fournisseur = 'toutes' au lieu de 'eau_electricite' |
| `llama3.2:3b` | صيفط لفاطمة 200 درهم | arabe | virement | beneficiaire = 'Fatima' au lieu de 'فاطمة' |
| `llama3.2:3b` | حول 300 درهم لفاطمة لحلو | arabe | virement | beneficiaire = 'Fatima' au lieu de 'فاطمة' |
| `llama3.2:3b` | شحال كتاخذ البنكة على كل عملية؟ | arabe | faq | outil consulter_solde au lieu de question_faq |
| `llama3.2:3b` | ila sifet l chi wa7ed daba, kaywsel f nefs nhar ? | latin | faq | outil faire_virement au lieu de question_faq |
| `llama3.2:3b` | Est-ce que je peux changer mon plafond de virement ? | francais | faq | outil consulter_plafond au lieu de question_faq |
| `llama3.2:3b` | بغيت نخلص فاتورة | arabe | floue | fournisseur inventé : 'eau_electricite' |
| `llama3.2:3b` | dir liya virement 3afak | latin | floue | beneficiaire inventé : 'liya' |
| `llama3.2:3b` | bghit nkhallas wa7d l facture | latin | floue | fournisseur inventé : 'eau_electricite' |
| `llama3.2:3b` | شنو هي العاصمة ديال اليابان؟ | arabe | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | 3tini chi nokta | latin | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | écris-moi un email l mudir dyali | melange | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = 'nefs l wa7ed' au lieu de 'Fatima' |
| `llama3.2:3b` | w chhal b9a liya ? | melange | suite | outil analyser_depenses au lieu de consulter_solde ; categorie inventé : 'toutes' |
| `llama3.2:3b` | bghit ncommandi chéquier jdid | melange | non_disponible | outil payer_facture au lieu de None |
| `llama3.2:3b` | ch7al men bénéficiaire 3ndi ? | melange | beneficiaires | outil None au lieu de lister_beneficiaires |
| `llama3.2:3b` | chhal srefti had chhar ? | latin | depenses | categorie inventé : 'null' |
| `llama3.2:3b` | شحال صرفت الشهر اللي فات؟ | arabe | depenses | periode = 'ce_mois' au lieu de 'mois_dernier' |
| `llama3.2:3b` | fin mchaw flousi had chhar ? | latin | depenses | periode = 'fin mchaw flousi' au lieu de 'ce_mois' ; categorie inventé : 'null' |
| `llama3.2:3b` | شحال خسرت فالطاكسي هاد الشهر؟ | arabe | depenses | periode = 'mois_dernier' au lieu de 'ce_mois' |
| `llama3.2:3b` | chofli solde w les factures li mazal | melange | plusieurs | outils ['consulter_solde'] au lieu de ['consulter_solde', 'lister_factures'] |
| `llama3.2:3b` | شحال عندي فالحساب و شنو هي آخر العمليات؟ | arabe | plusieurs | outils ['lister_transactions'] au lieu de ['consulter_solde', 'lister_transactions'] |
| `llama3.2:3b` | 3tini le solde w le plafond dyal virement | melange | plusieurs | outils ['consulter_solde', 'consulter_plafond', 'lister_factures'] au lieu de ['consulter_solde', 'consulter_plafond'] |
| `llama3.2:3b` | chhal 3ndi f l compte daba ? | latin | solde | outil analyser_depenses au lieu de consulter_solde ; categorie inventé : '3ndi' |
| `llama3.2:3b` | bghit ndir virement | latin | floue | outil question_faq au lieu de faire_virement |
| `llama3.2:3b` | chkoun rbe7 l'match dyal lbare7 ? | latin | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | chofe liya solde dyali chhale fihe + la liste dyal beneficiers 3ndi fl compte | latin | plusieurs | outils ['consulter_solde'] au lieu de ['consulter_solde', 'lister_beneficiaires'] |
| `qwen3:4b-instruct` | achno drt b lflous f had l'ayam ? | latin | operations | outil question_faq au lieu de lister_transactions |
| `qwen3:4b-instruct` | شنو خلصت هاد الأيام؟ | arabe | operations | outil lister_factures au lieu de lister_transactions |
| `qwen3:4b-instruct` | بغيت نخلص فاتورة الانترنيت | arabe | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'internet' |
| `qwen3:4b-instruct` | dir liya paiement dyal facture lma | latin | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'eau_electricite' |
| `qwen3:4b-instruct` | khalless ga3 les factures li 3liya | melange | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:4b-instruct` | خلص ليا كاع الفواتير | arabe | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:4b-instruct` | Envoie 150 dirhams à Fatima | francais | virement | outil lister_beneficiaires au lieu de faire_virement ; beneficiaire = None au lieu de 'Fatima' ; montant = None au lieu de 150 |
| `qwen3:4b-instruct` | bghit nsifet l Fatima | latin | virement | outil lister_beneficiaires au lieu de faire_virement ; beneficiaire = None au lieu de 'Fatima' |
| `qwen3:4b-instruct` | sifet 400 dh | latin | virement | outil lister_beneficiaires au lieu de faire_virement ; montant = None au lieu de 400 |
| `qwen3:4b-instruct` | بغيت نخلص فاتورة | arabe | floue | outil question_faq au lieu de payer_facture |
| `qwen3:4b-instruct` | dir liya virement 3afak | latin | floue | outil lister_beneficiaires au lieu de faire_virement |
| `qwen3:4b-instruct` | bghit nkhallas wa7d l facture | latin | floue | outil question_faq au lieu de payer_facture |
| `qwen3:4b-instruct` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = 'nef' au lieu de 'Fatima' |
| `qwen3:4b-instruct` | w chhal b9a liya ? | melange | suite | outil analyser_depenses au lieu de consulter_solde ; categorie inventé : 'restaurant' |
| `qwen3:4b-instruct` | شحال صرفت الشهر اللي فات؟ | arabe | depenses | periode = 'ce_mois' au lieu de 'mois_dernier' |
| `qwen3:4b-instruct` | bghit ndir virement | latin | floue | outil None au lieu de faire_virement |
