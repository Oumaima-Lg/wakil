# Benchmark darija de Wakil : résultats mesurés

Généré le 01/11/2026 par `evals/benchmark/rapport.py`, à partir de promptfoo. Données 100 % fictives.

**Ce qui est mesuré** : l'étape 1 de Wakil, par le vrai chemin de l'agent (même prompt, mêmes outils MCP, même historique). Une réponse est réussie si le LLM choisit le bon outil, avec les paramètres attendus, sans rien inventer. Aucun outil n'est exécuté.

**Les questions** : 113 jamais vues (paquet « test », qui donne la note) et 57 déjà utilisées pour régler Wakil (paquet « mise au point », score optimiste, donné à part).

**La machine** : Google Colab, GPU NVIDIA T4 (16 Go). Les temps de réponse en dépendent ; les modèles comparés sont toujours mesurés sur la même machine.

## Classement

| Modèle | Bon outil (test) | Outil et paramètres justes (test) | Mise au point (outil et paramètres) | Temps médian | Temps p95 | Jetons par question | JSON illisible (mode json) |
|---|---|---|---|---|---|---|---|
| `atlas-chat:9b` | 85 % (96/113) | **81 % (91/113)** | 56 % (32/57) | 1.6 s | 2.3 s | 1073 | 0 |
| `qwen3:4b-instruct` | 83 % (94/113) | **78 % (88/113)** | 44 % (25/57) | 0.4 s | 1.7 s | 1721 | 0 |
| `qwen3:8b` | 80 % (90/113) | **73 % (82/113)** | 26 % (15/57) | 0.7 s | 2.3 s | 1528 | 0 |

## Comparaison question par question (paquet test)

Sur les questions où deux modèles ne sont pas d'accord : si p est petit (moins de 0,05), l'écart n'est probablement pas dû au hasard.

| Modèle A | Modèle B | Seul A réussit | Seul B réussit | p (McNemar) |
|---|---|---|---|---|
| `atlas-chat:9b` | `qwen3:4b-instruct` | 14 | 11 | 0.690 |
| `atlas-chat:9b` | `qwen3:8b` | 17 | 8 | 0.108 |
| `qwen3:4b-instruct` | `qwen3:8b` | 11 | 5 | 0.210 |

## Par auteur des questions (paquet test)

| Modèle | écrites par Oumaima | générées, relues par Oumaima |
|---|---|---|
| `atlas-chat:9b` | 80 % (28/35) | 81 % (63/78) |
| `qwen3:4b-instruct` | 66 % (23/35) | 83 % (65/78) |
| `qwen3:8b` | 71 % (25/35) | 73 % (57/78) |

## Par écriture (tous paquets)

| Modèle | arabe | latin | melange | francais | anglais | arabe_standard |
|---|---|---|---|---|---|---|
| `atlas-chat:9b` | 79 % (26/33) | 67 % (38/57) | 68 % (27/40) | 80 % (16/20) | 80 % (8/10) | 80 % (8/10) |
| `qwen3:4b-instruct` | 52 % (17/33) | 56 % (32/57) | 72 % (29/40) | 75 % (15/20) | 100 % (10/10) | 100 % (10/10) |
| `qwen3:8b` | 52 % (17/33) | 46 % (26/57) | 58 % (23/40) | 65 % (13/20) | 90 % (9/10) | 90 % (9/10) |

## Par catégorie (tous paquets)

| Modèle | beneficiaires | cartes | depenses | factures | faq | floue | hors_sujet | non_disponible | operations | paiement | plafond | plusieurs | solde | suite | virement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `atlas-chat:9b` | 100 % (7/7) | 83 % (5/6) | 100 % (8/8) | 100 % (8/8) | 56 % (31/55) | 75 % (3/4) | 18 % (2/11) | 0 % (0/3) | 60 % (6/10) | 87 % (13/15) | 100 % (4/4) | 100 % (6/6) | 100 % (14/14) | 60 % (3/5) | 93 % (13/14) |
| `qwen3:4b-instruct` | 100 % (7/7) | 100 % (6/6) | 88 % (7/8) | 100 % (8/8) | 38 % (21/55) | 0 % (0/4) | 82 % (9/11) | 67 % (2/3) | 70 % (7/10) | 73 % (11/15) | 100 % (4/4) | 100 % (6/6) | 93 % (13/14) | 40 % (2/5) | 71 % (10/14) |
| `qwen3:8b` | 100 % (7/7) | 100 % (6/6) | 88 % (7/8) | 88 % (7/8) | 11 % (6/55) | 0 % (0/4) | 91 % (10/11) | 67 % (2/3) | 10 % (1/10) | 73 % (11/15) | 100 % (4/4) | 100 % (6/6) | 93 % (13/14) | 60 % (3/5) | 100 % (14/14) |

## Échecs du paquet test

| Modèle | Question | Écriture | Catégorie | Pourquoi |
|---|---|---|---|---|
| `atlas-chat:9b` | achno drt b lflous f had l'ayam ? | latin | operations | outil analyser_depenses au lieu de lister_transactions |
| `atlas-chat:9b` | شنو خلصت هاد الأيام؟ | arabe | operations | outil analyser_depenses au lieu de lister_transactions |
| `atlas-chat:9b` | خلص ليا كاع الفواتير | arabe | paiement | fournisseur = 'tout' au lieu de 'toutes' |
| `atlas-chat:9b` | ila sifet l chi wa7ed daba, kaywsel f nefs nhar ? | latin | faq | outil faire_virement au lieu de question_faq |
| `atlas-chat:9b` | bghit nkhallas wa7d l facture | latin | floue | fournisseur inventé : 'eau_electricite' |
| `atlas-chat:9b` | شنو هي العاصمة ديال اليابان؟ | arabe | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:9b` | 3tini chi nokta | latin | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:9b` | écris-moi un email l mudir dyali | melange | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:9b` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = None au lieu de 'Fatima' ; montant = None au lieu de 100 |
| `atlas-chat:9b` | w chhal b9a liya ? | melange | suite | outil analyser_depenses au lieu de consulter_solde |
| `atlas-chat:9b` | bghit ncommandi chéquier jdid | melange | non_disponible | outil question_faq au lieu de None |
| `atlas-chat:9b` | بغيت نبدل كلمة السر ديال التطبيق | arabe | non_disponible | outil question_faq au lieu de None |
| `atlas-chat:9b` | Show me my last transactions | anglais | operations | mois inventé : 'ce_mois' |
| `atlas-chat:9b` | أرني آخر العمليات في حسابي | arabe_standard | operations | mois inventé : 'ce_mois' |
| `atlas-chat:9b` | اكتب لي قصيدة عن البحر | arabe_standard | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:9b` | chkoun rbe7 l'match dyal lbare7 ? | latin | hors_sujet | outil question_faq au lieu de None |
| `atlas-chat:9b` | Ma carte est deja bloquée ? | francais | cartes | outil question_faq au lieu de consulter_cartes |
| `atlas-chat:9b` | dibloque liya la carte dyali | melange | faq | outil bloquer_carte au lieu de question_faq |
| `atlas-chat:9b` | Merci de débloquer ma carte | francais | faq | outil None au lieu de question_faq |
| `atlas-chat:9b` | zide liya benifciaire jdide | latin | faq | outil lister_beneficiaires au lieu de question_faq |
| `atlas-chat:9b` | bgjite nzide benifiaire | latin | faq | outil lister_beneficiaires au lieu de question_faq |
| `atlas-chat:9b` | je veux ajouter un bénéficiare | francais | faq | outil lister_beneficiaires au lieu de question_faq |
| `qwen3:4b-instruct` | achno drt b lflous f had l'ayam ? | latin | operations | outil question_faq au lieu de lister_transactions |
| `qwen3:4b-instruct` | شنو خلصت هاد الأيام؟ | arabe | operations | outil lister_factures au lieu de lister_transactions |
| `qwen3:4b-instruct` | dir liya paiement dyal facture lma | latin | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'eau_electricite' |
| `qwen3:4b-instruct` | khalless ga3 les factures li 3liya | melange | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:4b-instruct` | خلص ليا كاع الفواتير | arabe | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:4b-instruct` | صيفط لفاطمة 200 درهم | arabe | virement | beneficiaire = 'fatima' au lieu de 'فاطمة' |
| `qwen3:4b-instruct` | wach Wakil kaykhdem nhar l3id ? | latin | faq | outil None au lieu de question_faq |
| `qwen3:4b-instruct` | واش هاد البنك ديال بصح ولا غير تجربة؟ | arabe | faq | outil None au lieu de question_faq |
| `qwen3:4b-instruct` | بغيت نخلص فاتورة | arabe | floue | outil lister_factures au lieu de payer_facture |
| `qwen3:4b-instruct` | bghit nkhallas wa7d l facture | latin | floue | outil lister_factures au lieu de payer_facture |
| `qwen3:4b-instruct` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = 'nef' au lieu de 'Fatima' |
| `qwen3:4b-instruct` | w chhal b9a liya ? | melange | suite | outil analyser_depenses au lieu de consulter_solde ; categorie inventé : 'restaurant' |
| `qwen3:4b-instruct` | شحال صرفت الشهر اللي فات؟ | arabe | depenses | periode = 'ce_mois' au lieu de 'mois_dernier' |
| `qwen3:4b-instruct` | bghit ndir virement | latin | floue | outil None au lieu de faire_virement |
| `qwen3:4b-instruct` | Bghite nsifte 2000 DH l Fatima, wach kayn solde kafi ? | latin | solde | outil lister_beneficiaires au lieu de consulter_solde |
| `qwen3:4b-instruct` | dibloque liya la carte dyali | melange | faq | outil bloquer_carte au lieu de question_faq ; carte inventé : '1234' |
| `qwen3:4b-instruct` | Merci de débloquer ma carte | francais | faq | outil None au lieu de question_faq |
| `qwen3:4b-instruct` | chno kadire f 7yatke ? | latin | faq | outil None au lieu de question_faq |
| `qwen3:4b-instruct` | qu'est ce que tu fais dans ta vie ? | francais | faq | outil None au lieu de question_faq |
| `qwen3:4b-instruct` | zide liya benifciaire jdide | latin | faq | outil lister_beneficiaires au lieu de question_faq |
| `qwen3:4b-instruct` | bgjite nzide benifiaire | latin | faq | outil lister_beneficiaires au lieu de question_faq |
| `qwen3:4b-instruct` | je veux ajouter un bénéficiare | francais | faq | outil None au lieu de question_faq |
| `qwen3:4b-instruct` | bghite nsifte 2000 dh liya ana fl compte dyali. | latin | virement | beneficiaire inventé : 'Ali' |
| `qwen3:4b-instruct` | je veux envoyer 2000 dh à moi-même dans mon compte. | francais | virement | beneficiaire inventé : 'self' |
| `qwen3:4b-instruct` | sf mzn, daba sifte liha 456.78 dh | latin | suite | beneficiaire inventé : 'Ahmed' |
| `qwen3:8b` | ورّيني آخر العمليات اللي دازو فالحساب | arabe | operations | mois inventé : 12 |
| `qwen3:8b` | achno drt b lflous f had l'ayam ? | latin | operations | outil None au lieu de lister_transactions |
| `qwen3:8b` | affichili les dernières dépenses dyali | melange | operations | mois inventé : 1 |
| `qwen3:8b` | شنو خلصت هاد الأيام؟ | arabe | operations | outil analyser_depenses au lieu de lister_transactions ; categorie inventé : 'factures' |
| `qwen3:8b` | chouf liya l7arakat dyal l compte | latin | operations | outil consulter_cartes au lieu de lister_transactions |
| `qwen3:8b` | ach men factures mazal 3liya ? | latin | factures | outil None au lieu de lister_factures |
| `qwen3:8b` | dir liya paiement dyal facture lma | latin | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'eau_electricite' |
| `qwen3:8b` | khalless ga3 les factures li 3liya | melange | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:8b` | خلص ليا كاع الفواتير | arabe | paiement | outil lister_factures au lieu de payer_facture ; fournisseur = None au lieu de 'toutes' |
| `qwen3:8b` | wach Wakil kaykhdem nhar l3id ? | latin | faq | outil None au lieu de question_faq |
| `qwen3:8b` | si quelqu'un m'appelle w ytleb code SMS, chno ndir ? | melange | faq | outil None au lieu de question_faq |
| `qwen3:8b` | واش هاد البنك ديال بصح ولا غير تجربة؟ | arabe | faq | outil None au lieu de question_faq |
| `qwen3:8b` | ila sifet l chi wa7ed daba, kaywsel f nefs nhar ? | latin | faq | outil faire_virement au lieu de question_faq ; montant inventé : 500 |
| `qwen3:8b` | Est-ce que je peux changer mon plafond de virement ? | francais | faq | outil None au lieu de question_faq |
| `qwen3:8b` | بغيت نخلص فاتورة | arabe | floue | outil lister_factures au lieu de payer_facture |
| `qwen3:8b` | bghit nkhallas wa7d l facture | latin | floue | outil lister_factures au lieu de payer_facture |
| `qwen3:8b` | w 3awed 100 dh l nefs l wa7ed | latin | suite | beneficiaire = 'nefs' au lieu de 'Fatima' |
| `qwen3:8b` | w chhal b9a liya ? | melange | suite | outil analyser_depenses au lieu de consulter_solde ; categorie inventé : 'retraits' |
| `qwen3:8b` | chhal srefti had chhar ? | latin | depenses | categorie inventé : 'toutes' |
| `qwen3:8b` | Show me my last transactions | anglais | operations | mois inventé : 12 |
| `qwen3:8b` | أرني آخر العمليات في حسابي | arabe_standard | operations | mois inventé : 12 |
| `qwen3:8b` | bghit nchouf akhir les opérations dyali | melange | operations | mois inventé : 12 |
| `qwen3:8b` | bghit ndir virement | latin | floue | beneficiaire inventé : 'nom du bénéficiaire' ; montant inventé : 0 |
| `qwen3:8b` | Bghite nsifte 2000 DH l Fatima, wach kayn solde kafi ? | latin | solde | outil faire_virement au lieu de consulter_solde |
| `qwen3:8b` | dibloque liya la carte dyali | melange | faq | outil bloquer_carte au lieu de question_faq ; carte inventé : '4321' |
| `qwen3:8b` | Merci de débloquer ma carte | francais | faq | outil None au lieu de question_faq |
| `qwen3:8b` | chno kadire f 7yatke ? | latin | faq | outil None au lieu de question_faq |
| `qwen3:8b` | qu'est ce que tu fais dans ta vie ? | francais | faq | outil None au lieu de question_faq |
| `qwen3:8b` | zide liya benifciaire jdide | latin | faq | outil lister_beneficiaires au lieu de question_faq |
| `qwen3:8b` | bgjite nzide benifiaire | latin | faq | outil lister_beneficiaires au lieu de question_faq |
| `qwen3:8b` | je veux ajouter un bénéficiare | francais | faq | outil None au lieu de question_faq |
