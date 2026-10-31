# Benchmark darija de Wakil : résultats mesurés

Généré le 31/10/2026 par `evals/benchmark/rapport.py`, à partir de promptfoo. Données 100 % fictives.

**Ce qui est mesuré** : l'étape 1 de Wakil, par le vrai chemin de l'agent (même prompt, mêmes outils MCP, même historique). Une réponse est réussie si le LLM choisit le bon outil, avec les paramètres attendus, sans rien inventer. Aucun outil n'est exécuté.

**Les questions** : 90 jamais vues (paquet « test », qui donne la note) et 57 déjà utilisées pour régler Wakil (paquet « mise au point », score optimiste, donné à part).

## Classement

| Modèle | Bon outil (test) | Outil et paramètres justes (test) | Mise au point (outil et paramètres) | Temps médian | Temps p95 | Jetons par question | JSON illisible (mode json) |
|---|---|---|---|---|---|---|---|
| `atlas-chat:2b` | 70 % (63/90) | **54 % (49/90)** | 32 % (18/57) | 2.0 s | 7.8 s | 903 | 4 |
| `atlas-chat:9b` | 91 % (82/90) | **86 % (77/90)** | 56 % (32/57) | 8.1 s | 13.7 s | 894 | 0 |
| `llama3.2:3b` | 71 % (64/90) | **58 % (52/90)** | 58 % (33/57) | 0.7 s | 1.7 s | 1307 | 0 |
| `qwen3:4b-instruct` | 87 % (78/90) | **84 % (76/90)** | 47 % (27/57) | 2.6 s | 9.1 s | 1446 | 0 |
| `qwen3:8b` | 83 % (75/90) | **77 % (69/90)** | 30 % (17/57) | 7.3 s | 20.6 s | 1284 | 0 |

## Comparaison question par question (paquet test)

Sur les questions où deux modèles ne sont pas d'accord : si p est petit (moins de 0,05), l'écart n'est probablement pas dû au hasard.

| Modèle A | Modèle B | Seul A réussit | Seul B réussit | p (McNemar) |
|---|---|---|---|---|
| `atlas-chat:2b` | `atlas-chat:9b` | 3 | 31 | 0.000 |
| `atlas-chat:2b` | `llama3.2:3b` | 16 | 19 | 0.736 |
| `atlas-chat:2b` | `qwen3:4b-instruct` | 1 | 28 | 0.000 |
| `atlas-chat:2b` | `qwen3:8b` | 2 | 22 | 0.000 |
| `atlas-chat:9b` | `llama3.2:3b` | 28 | 3 | 0.000 |
| `atlas-chat:9b` | `qwen3:4b-instruct` | 8 | 7 | 1.000 |
| `atlas-chat:9b` | `qwen3:8b` | 14 | 6 | 0.115 |
| `llama3.2:3b` | `qwen3:4b-instruct` | 5 | 29 | 0.000 |
| `llama3.2:3b` | `qwen3:8b` | 5 | 22 | 0.002 |
| `qwen3:4b-instruct` | `qwen3:8b` | 10 | 3 | 0.092 |

## Par écriture (tous paquets)

| Modèle | arabe | latin | melange | francais | anglais | arabe_standard |
|---|---|---|---|---|---|---|
| `atlas-chat:2b` | 45 % (15/33) | 29 % (14/48) | 42 % (15/36) | 80 % (8/10) | 90 % (9/10) | 60 % (6/10) |
| `atlas-chat:9b` | 79 % (26/33) | 65 % (31/48) | 67 % (24/36) | 90 % (9/10) | 100 % (10/10) | 90 % (9/10) |
| `llama3.2:3b` | 42 % (14/33) | 52 % (25/48) | 61 % (22/36) | 80 % (8/10) | 90 % (9/10) | 70 % (7/10) |
| `qwen3:4b-instruct` | 61 % (20/33) | 60 % (29/48) | 75 % (27/36) | 80 % (8/10) | 90 % (9/10) | 100 % (10/10) |
| `qwen3:8b` | 52 % (17/33) | 42 % (20/48) | 64 % (23/36) | 70 % (7/10) | 100 % (10/10) | 90 % (9/10) |

## Par catégorie (tous paquets)

| Modèle | beneficiaires | depenses | factures | faq | floue | hors_sujet | non_disponible | operations | paiement | plafond | plusieurs | solde | suite | virement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `atlas-chat:2b` | 100 % (6/6) | 38 % (3/8) | 75 % (6/8) | 23 % (11/48) | 0 % (0/4) | 73 % (8/11) | 33 % (1/3) | 50 % (5/10) | 13 % (2/15) | 100 % (4/4) | 100 % (6/6) | 75 % (6/8) | 25 % (1/4) | 67 % (8/12) |
| `atlas-chat:9b` | 100 % (6/6) | 100 % (8/8) | 100 % (8/8) | 60 % (29/48) | 50 % (2/4) | 27 % (3/11) | 0 % (0/3) | 90 % (9/10) | 73 % (11/15) | 100 % (4/4) | 100 % (6/6) | 100 % (8/8) | 75 % (3/4) | 100 % (12/12) |
| `llama3.2:3b` | 83 % (5/6) | 38 % (3/8) | 88 % (7/8) | 58 % (28/48) | 0 % (0/4) | 0 % (0/11) | 33 % (1/3) | 60 % (6/10) | 87 % (13/15) | 50 % (2/4) | 33 % (2/6) | 88 % (7/8) | 50 % (2/4) | 75 % (9/12) |
| `qwen3:4b-instruct` | 100 % (6/6) | 88 % (7/8) | 100 % (8/8) | 56 % (27/48) | 0 % (0/4) | 82 % (9/11) | 67 % (2/3) | 80 % (8/10) | 60 % (9/15) | 100 % (4/4) | 100 % (6/6) | 75 % (6/8) | 50 % (2/4) | 75 % (9/12) |
| `qwen3:8b` | 100 % (6/6) | 50 % (4/8) | 100 % (8/8) | 15 % (7/48) | 0 % (0/4) | 91 % (10/11) | 100 % (3/3) | 60 % (6/10) | 73 % (11/15) | 100 % (4/4) | 100 % (6/6) | 100 % (8/8) | 50 % (2/4) | 92 % (11/12) |

## Échecs du paquet test

| Modèle | Question | Écriture | Catégorie | Pourquoi |
|---|---|---|---|---|
| `atlas-chat:2b` | chhal fih l compte dyali daba | latin | solde | outil None au lieu de consulter_solde |
| `atlas-chat:2b` | achno drt b lflous f had l'ayam ? | latin | operations | outil None au lieu de lister_transactions |
| `atlas-chat:2b` | affichili les dernières dépenses dyali | melange | operations | outil None au lieu de lister_transactions |
| `atlas-chat:2b` | شنو خلصت هاد الأيام؟ | arabe | operations | outil payer_facture au lieu de lister_transactions ; montant inventé : '249' |
| `atlas-chat:2b` | chouf liya l7arakat dyal l compte | latin | operations | outil None au lieu de lister_transactions |
| `atlas-chat:2b` | ach men factures mazal 3liya ? | latin | factures | outil None au lieu de lister_factures |
| `atlas-chat:2b` | خلص ليا فاتورة الضو والما | arabe | paiement | montant inventé : '249' |
| `atlas-chat:2b` | khallas liya l internet 3afak | latin | paiement | outil None au lieu de payer_facture ; fournisseur = None au lieu de 'internet' |
| `atlas-chat:2b` | règle-lia la facture d'internet | melange | paiement | outil faire_virement au lieu de payer_facture ; fournisseur = None au lieu de 'internet' ; montant inventé : '249' |
| `atlas-chat:2b` | بغيت نخلص فاتورة الانترنيت | arabe | paiement | montant inventé : '249' |
| `atlas-chat:2b` | dir liya paiement dyal facture lma | latin | paiement | outil None au lieu de payer_facture ; fournisseur = None au lieu de 'eau_electricite' |
| `atlas-chat:2b` | payi liya la facture dyal l'électricité | melange | paiement | montant inventé : '249' |
| `atlas-chat:2b` | khalless ga3 les factures li 3liya | melange | paiement | outil None au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `atlas-chat:2b` | خلص ليا كاع الفواتير | arabe | paiement | fournisseur = 'eau_electricite' au lieu de 'toutes' ; montant inventé : '249' |
| `atlas-chat:2b` | صيفط لفاطمة 200 درهم | arabe | virement | beneficiaire = 'فاتمة' au lieu de 'فاطمة' |
| `atlas-chat:2b` | حول 300 درهم لفاطمة لحلو | arabe | virement | beneficiaire = 'فاتمة' au lieu de 'فاطمة' |
| `atlas-chat:2b` | wach Wakil kaykhdem nhar l3id ? | latin | faq | outil None au lieu de question_faq |
| `atlas-chat:2b` | واش هاد البنك ديال بصح ولا غير تجربة؟ | arabe | faq | outil None au lieu de question_faq |
| `atlas-chat:2b` | ila sifet l chi wa7ed daba, kaywsel f nefs nhar ? | latin | faq | outil faire_virement au lieu de question_faq ; montant inventé : '100' |
| `atlas-chat:2b` | Est-ce que je peux changer mon plafond de virement ? | francais | faq | outil consulter_plafond au lieu de question_faq |
| `atlas-chat:2b` | بغيت نخلص فاتورة | arabe | floue | fournisseur inventé : 'eau_electricite' ; montant inventé : '249' |
| `atlas-chat:2b` | bghit nkhallas wa7d l facture | latin | floue | fournisseur inventé : 'eau_electricite' ; montant inventé : '249' |
| `atlas-chat:2b` | écris-moi un email l mudir dyali | melange | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:2b` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = None au lieu de 'Fatima' ; montant = None au lieu de 100 |
| `atlas-chat:2b` | w chhal b9a liya ? | melange | suite | outil lister_transactions au lieu de consulter_solde |
| `atlas-chat:2b` | بغيت نبدل كلمة السر ديال التطبيق | arabe | non_disponible | outil question_faq au lieu de None |
| `atlas-chat:2b` | chhal srefti had chhar ? | latin | depenses | outil None au lieu de analyser_depenses |
| `atlas-chat:2b` | شحال صرفت الشهر اللي فات؟ | arabe | depenses | outil None au lieu de analyser_depenses ; periode = None au lieu de 'mois_dernier' |
| `atlas-chat:2b` | ch7al mchat 3liya f restaurant had chhar | latin | depenses | periode = 'mois_dernier' au lieu de 'ce_mois' |
| `atlas-chat:2b` | fin mchaw flousi had chhar ? | latin | depenses | outil None au lieu de analyser_depenses |
| `atlas-chat:2b` | Pay my internet bill | anglais | paiement | montant inventé : '249' |
| `atlas-chat:2b` | ادفع فاتورة الماء والكهرباء | arabe_standard | paiement | montant inventé : '249' |
| `atlas-chat:2b` | حوّل 500 درهم إلى فاطمة | arabe_standard | virement | beneficiaire = 'فاتمة' au lieu de 'فاطمة' |
| `atlas-chat:2b` | كم أنفقت في الشهر الماضي؟ | arabe_standard | depenses | outil None au lieu de analyser_depenses ; periode = None au lieu de 'mois_dernier' |
| `atlas-chat:2b` | اكتب لي قصيدة عن البحر | arabe_standard | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:2b` | bghit nchouf akhir les opérations dyali | melange | operations | outil None au lieu de lister_transactions |
| `atlas-chat:2b` | wach 3ndi chi factures mazal ? | latin | factures | outil None au lieu de lister_factures |
| `atlas-chat:2b` | khelless liya l'internet | melange | paiement | montant inventé : '249' |
| `atlas-chat:2b` | wach kayn chi frais ila sifet l bank khra ? | latin | faq | outil None au lieu de question_faq |
| `atlas-chat:2b` | bghit ndir virement | latin | floue | outil None au lieu de faire_virement |
| `atlas-chat:2b` | w les factures ? | melange | suite | outil consulter_solde au lieu de lister_factures |
| `atlas-chat:9b` | achno drt b lflous f had l'ayam ? | latin | operations | outil analyser_depenses au lieu de lister_transactions |
| `atlas-chat:9b` | dir liya paiement dyal facture lma | latin | paiement | fournisseur = 'mobile' au lieu de 'eau_electricite' |
| `atlas-chat:9b` | khalless ga3 les factures li 3liya | melange | paiement | fournisseur = 'tout' au lieu de 'toutes' |
| `atlas-chat:9b` | خلص ليا كاع الفواتير | arabe | paiement | fournisseur = 'tout' au lieu de 'toutes' |
| `atlas-chat:9b` | ila sifet l chi wa7ed daba, kaywsel f nefs nhar ? | latin | faq | outil faire_virement au lieu de question_faq |
| `atlas-chat:9b` | bghit nkhallas wa7d l facture | latin | floue | fournisseur inventé : 'eau_electricite' |
| `atlas-chat:9b` | شنو هي العاصمة ديال اليابان؟ | arabe | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:9b` | 3tini chi nokta | latin | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:9b` | écris-moi un email l mudir dyali | melange | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:9b` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = None au lieu de 'Fatima' ; montant = None au lieu de 100 |
| `atlas-chat:9b` | bghit ncommandi chéquier jdid | melange | non_disponible | outil question_faq au lieu de None |
| `atlas-chat:9b` | بغيت نبدل كلمة السر ديال التطبيق | arabe | non_disponible | outil question_faq au lieu de None |
| `atlas-chat:9b` | اكتب لي قصيدة عن البحر | arabe_standard | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | شحال عندي فالكونط؟ | arabe | solde | outil question_faq au lieu de consulter_solde |
| `llama3.2:3b` | شحال هو البلافون ديال الكونط ديالي؟ | arabe | plafond | outil analyser_depenses au lieu de consulter_plafond ; categorie inventé : 'null' |
| `llama3.2:3b` | achno drt b lflous f had l'ayam ? | latin | operations | outil analyser_depenses au lieu de lister_transactions ; categorie inventé : 'chhal srefti' |
| `llama3.2:3b` | affichili les dernières dépenses dyali | melange | operations | outil analyser_depenses au lieu de lister_transactions ; categorie inventé : 'dyali' |
| `llama3.2:3b` | شنو خلصت هاد الأيام؟ | arabe | operations | outil analyser_depenses au lieu de lister_transactions ; categorie inventé : 'null' |
| `llama3.2:3b` | chouf liya l7arakat dyal l compte | latin | operations | outil consulter_solde au lieu de lister_transactions |
| `llama3.2:3b` | les factures en attente dyali chno homa ? | melange | factures | outil None au lieu de lister_factures |
| `llama3.2:3b` | خلص ليا فاتورة الضو والما | arabe | paiement | montant inventé : 249 |
| `llama3.2:3b` | dir liya paiement dyal facture lma | latin | paiement | fournisseur = 'toutes' au lieu de 'eau_electricite' |
| `llama3.2:3b` | صيفط لفاطمة 200 درهم | arabe | virement | beneficiaire = 'Fatima' au lieu de 'فاطمة' |
| `llama3.2:3b` | حول 300 درهم لفاطمة لحلو | arabe | virement | outil payer_facture au lieu de faire_virement ; beneficiaire = None au lieu de 'فاطمة' |
| `llama3.2:3b` | شحال كتاخذ البنكة على كل عملية؟ | arabe | faq | outil consulter_solde au lieu de question_faq |
| `llama3.2:3b` | ila sifet l chi wa7ed daba, kaywsel f nefs nhar ? | latin | faq | outil faire_virement au lieu de question_faq |
| `llama3.2:3b` | Est-ce que je peux changer mon plafond de virement ? | francais | faq | outil consulter_plafond au lieu de question_faq |
| `llama3.2:3b` | بغيت نخلص فاتورة | arabe | floue | fournisseur inventé : 'eau_electricite' |
| `llama3.2:3b` | bghit nkhallas wa7d l facture | latin | floue | fournisseur inventé : 'eau_electricite' |
| `llama3.2:3b` | شنو هي العاصمة ديال اليابان؟ | arabe | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | 3tini chi nokta | latin | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | écris-moi un email l mudir dyali | melange | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = 'nefs l wa7ed' au lieu de 'Fatima' |
| `llama3.2:3b` | w chhal b9a liya ? | melange | suite | outil analyser_depenses au lieu de consulter_solde ; categorie inventé : 'toutes' |
| `llama3.2:3b` | bghit ncommandi chéquier jdid | melange | non_disponible | outil lister_factures au lieu de None |
| `llama3.2:3b` | ch7al men bénéficiaire 3ndi ? | melange | beneficiaires | outil None au lieu de lister_beneficiaires |
| `llama3.2:3b` | chhal srefti had chhar ? | latin | depenses | categorie inventé : 'null' |
| `llama3.2:3b` | شحال صرفت الشهر اللي فات؟ | arabe | depenses | periode = 'ce_mois' au lieu de 'mois_dernier' |
| `llama3.2:3b` | fin mchaw flousi had chhar ? | latin | depenses | periode = 'fin mchaw flousi' au lieu de 'ce_mois' ; categorie inventé : 'null' |
| `llama3.2:3b` | شحال خسرت فالطاكسي هاد الشهر؟ | arabe | depenses | periode = 'mois_dernier' au lieu de 'ce_mois' |
| `llama3.2:3b` | chofli solde w les factures li mazal | melange | plusieurs | outils ['consulter_solde'] au lieu de ['consulter_solde', 'lister_factures'] |
| `llama3.2:3b` | شحال عندي فالحساب و شنو هي آخر العمليات؟ | arabe | plusieurs | outils ['lister_transactions'] au lieu de ['consulter_solde', 'lister_transactions'] |
| `llama3.2:3b` | 3tini le solde w le plafond dyal virement | melange | plusieurs | outils ['consulter_solde', 'consulter_plafond', 'lister_transactions'] au lieu de ['consulter_solde', 'consulter_plafond'] |
| `llama3.2:3b` | What's the weather like in Rabat tomorrow? | anglais | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | حوّل 500 درهم إلى فاطمة | arabe_standard | virement | beneficiaire = 'Faatma' au lieu de 'فاطمة' |
| `llama3.2:3b` | كم أنفقت في الشهر الماضي؟ | arabe_standard | depenses | categorie inventé : 'null' |
| `llama3.2:3b` | اكتب لي قصيدة عن البحر | arabe_standard | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | شحال هو الماكسيموم اللي نقدر نصيفط؟ | arabe | plafond | outil analyser_depenses au lieu de consulter_plafond ; categorie inventé : 'retraits' |
| `llama3.2:3b` | bghit ndir virement | latin | floue | outil question_faq au lieu de faire_virement |
| `llama3.2:3b` | chkoun rbe7 l'match dyal lbare7 ? | latin | hors_sujet | outil question_faq au lieu de None |
| `llama3.2:3b` | chofe liya solde dyali chhale fihe + la liste dyal beneficiers 3ndi fl compte | latin | plusieurs | outils ['consulter_solde'] au lieu de ['consulter_solde', 'lister_beneficiaires'] |
| `qwen3:4b-instruct` | chhal fih l compte dyali daba | latin | solde | outil question_faq au lieu de consulter_solde |
| `qwen3:4b-instruct` | achno drt b lflous f had l'ayam ? | latin | operations | outil question_faq au lieu de lister_transactions |
| `qwen3:4b-instruct` | شنو خلصت هاد الأيام؟ | arabe | operations | outil lister_factures au lieu de lister_transactions |
| `qwen3:4b-instruct` | règle-lia la facture d'internet | melange | paiement | outil question_faq au lieu de payer_facture ; fournisseur = None au lieu de 'internet' |
| `qwen3:4b-instruct` | dir liya paiement dyal facture lma | latin | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'eau_electricite' |
| `qwen3:4b-instruct` | khalless ga3 les factures li 3liya | melange | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:4b-instruct` | خلص ليا كاع الفواتير | arabe | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:4b-instruct` | bghit nkhallas dik l facture dyal 249 dirham | latin | paiement | outil question_faq au lieu de payer_facture ; montant = None au lieu de 249 |
| `qwen3:4b-instruct` | بغيت نخلص فاتورة | arabe | floue | outil question_faq au lieu de payer_facture |
| `qwen3:4b-instruct` | bghit nkhallas wa7d l facture | latin | floue | outil question_faq au lieu de payer_facture |
| `qwen3:4b-instruct` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = 'nef' au lieu de 'Fatima' |
| `qwen3:4b-instruct` | w chhal b9a liya ? | melange | suite | outil analyser_depenses au lieu de consulter_solde ; categorie inventé : 'restaurant' |
| `qwen3:4b-instruct` | شحال صرفت الشهر اللي فات؟ | arabe | depenses | periode = 'ce_mois' au lieu de 'mois_dernier' |
| `qwen3:4b-instruct` | bghit ndir virement | latin | floue | outil None au lieu de faire_virement |
| `qwen3:8b` | achno drt b lflous f had l'ayam ? | latin | operations | outil None au lieu de lister_transactions |
| `qwen3:8b` | affichili les dernières dépenses dyali | melange | operations | categorie inventé : 'dépenses' |
| `qwen3:8b` | شنو خلصت هاد الأيام؟ | arabe | operations | outil None au lieu de lister_transactions |
| `qwen3:8b` | chouf liya l7arakat dyal l compte | latin | operations | outil consulter_solde au lieu de lister_transactions |
| `qwen3:8b` | dir liya paiement dyal facture lma | latin | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'eau_electricite' |
| `qwen3:8b` | khalless ga3 les factures li 3liya | melange | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:8b` | خلص ليا كاع الفواتير | arabe | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:8b` | شحال كتاخذ البنكة على كل عملية؟ | arabe | faq | outil None au lieu de question_faq |
| `qwen3:8b` | wach Wakil kaykhdem nhar l3id ? | latin | faq | outil None au lieu de question_faq |
| `qwen3:8b` | si quelqu'un m'appelle w ytleb code SMS, chno ndir ? | melange | faq | outil None au lieu de question_faq |
| `qwen3:8b` | واش هاد البنك ديال بصح ولا غير تجربة؟ | arabe | faq | outil None au lieu de question_faq |
| `qwen3:8b` | ila sifet l chi wa7ed daba, kaywsel f nefs nhar ? | latin | faq | outil faire_virement au lieu de question_faq ; montant inventé : 500 |
| `qwen3:8b` | بغيت نخلص فاتورة | arabe | floue | outil lister_factures au lieu de payer_facture |
| `qwen3:8b` | bghit nkhallas wa7d l facture | latin | floue | outil lister_factures au lieu de payer_facture |
| `qwen3:8b` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = 'nefs' au lieu de 'Fatima' |
| `qwen3:8b` | w chhal b9a liya ? | melange | suite | outil analyser_depenses au lieu de consulter_solde ; categorie inventé : 'retraits' |
| `qwen3:8b` | chhal srefti had chhar ? | latin | depenses | categorie inventé : 'toutes' |
| `qwen3:8b` | شحال صرفت الشهر اللي فات؟ | arabe | depenses | categorie inventé : 'toutes' |
| `qwen3:8b` | fin mchaw flousi had chhar ? | latin | depenses | categorie inventé : 'factures' |
| `qwen3:8b` | كم أنفقت في الشهر الماضي؟ | arabe_standard | depenses | categorie inventé : 'toutes' |
| `qwen3:8b` | bghit ndir virement | latin | floue | outil lister_beneficiaires au lieu de faire_virement |
