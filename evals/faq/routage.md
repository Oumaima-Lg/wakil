# Choix de l'outil par le LLM : résultats mesurés

LLM : `qwen3:4b-instruct` · 48 questions · généré par `evals/faq/routage.py`. Seul le choix de l'outil est mesuré (étape 1) : ni la banque ni la FAQ ne sont appelées.

| Groupe | Bon outil choisi |
|---|---|
| Questions de FAQ → question_faq | 47 % (18/38) |
| Demandes sur le compte → leur outil | 80 % (4/5) |
| Hors sujet → aucun outil | 100 % (5/5) |

Questions de FAQ envoyées à `question_faq`, par écriture :

- arabe : 20 % (2/10)
- latin : 50 % (7/14)
- melange : 64 % (7/11)
- francais : 67 % (2/3)

Temps du choix (un appel au LLM) : médiane 3.8 s, maximum 71.2 s.

## Détail

| Question | Écriture | Attendu | Obtenu | |
|---|---|---|---|---|
| شحال كيتخلص الحساب فالشهر؟ | arabe | question_faq | question_faq | ✅ |
| واش نقدر نصيفط عشرين ألف درهم مرة وحدة؟ | arabe | question_faq | question_faq | ✅ |
| الفلوس اللي صيفطت لخويا إمتى غادي توصل؟ | arabe | question_faq | faire_virement | ❌ |
| بغيت نزيد صاحبي فالليستة باش نصيفط ليه | arabe | question_faq | (aucun) | ❌ |
| سرقو ليا البزطام والكارطة كانت فيه | arabe | question_faq | (aucun) | ❌ |
| واحد عيط ليا وطلب الكود اللي جاني فالميساج | arabe | question_faq | (aucun) | ❌ |
| كاينة شي عملية فالحساب ديالي ما عرفتهاش | arabe | question_faq | lister_transactions | ❌ |
| إلا ما كفاش الصولد واش غادي تخلص الفاتورة؟ | arabe | question_faq | consulter_solde | ❌ |
| واش المعلومات ديالي كتمشي لشي بلاصة؟ | arabe | question_faq | (aucun) | ❌ |
| واش نقدر نهضر معاك فالليل؟ | arabe | question_faq | (aucun) | ❌ |
| wach kaykhlsoni ila sifet l chi bank khra ? | latin | question_faq | (aucun) | ❌ |
| ch7al l7ed dyal l virement l wa7ed ? | latin | question_faq | question_faq | ✅ |
| sift lflous l mama, imta twslha ? | latin | question_faq | faire_virement | ❌ |
| kifach nkhelles facture dyal telephone ? | latin | question_faq | question_faq | ✅ |
| 3lach kaytl3 lia had l carte dyal confirmation ? | latin | question_faq | (aucun) | ❌ |
| carte dyali mab9atch 3endi, tal9at lia | latin | question_faq | (aucun) | ❌ |
| wach nsifet lik mot de passe bach tchouf l compte ? | latin | question_faq | (aucun) | ❌ |
| ma3endich flous bzaf, wach t9der tkhelles b credit ? | latin | question_faq | question_faq | ✅ |
| chno lkhdma li kadirha nta ? | latin | question_faq | (aucun) | ❌ |
| wach had l'application dyal bss7 wla ghi demo ? | latin | question_faq | question_faq | ✅ |
| les virements wach payants ? | melange | question_faq | question_faq | ✅ |
| le maximum li n9der nvirer f une seule fois ch7al ? | melange | question_faq | question_faq | ✅ |
| le virement kaykhd combien de temps ? | melange | question_faq | question_faq | ✅ |
| ajouter un nouveau bénéficiaire, wach possible ? | melange | question_faq | (aucun) | ❌ |
| la facture d'électricité, wach t9der tpayiha ? | melange | question_faq | lister_factures | ❌ |
| si je dis non f la confirmation chno kayw9e3 ? | melange | question_faq | (aucun) | ❌ |
| j'ai perdu ma carte, chno khassni ndir ? | melange | question_faq | question_faq | ✅ |
| kayna une opération bizarre f le relevé dyali | melange | question_faq | lister_transactions | ❌ |
| le découvert wach autorisé ? | melange | question_faq | question_faq | ✅ |
| Wakil disponible le weekend ? | melange | question_faq | question_faq | ✅ |
| bghite nzide benificaire | latin | question_faq | question_faq | ✅ |
| chnahiya fonction dyalke ? | latin | question_faq | question_faq | ✅ |
| quel est ton role ? | francais | question_faq | (aucun) | ❌ |
| quels sont tes services ? | francais | question_faq | question_faq | ✅ |
| 5adamate dyalke ? | latin | question_faq | (aucun) | ❌ |
| chno howa plafond dyali | latin | question_faq | question_faq | ✅ |
| comment ajouter un Bénéficiaire ? | francais | question_faq | question_faq | ✅ |
| kifache n payer une factuer ? | melange | question_faq | question_faq | ✅ |
| chhal bqa f compte dyali ? | latin | consulter_solde | consulter_solde | ✅ |
| شنو هوما آخر العمليات ديالي؟ | arabe | lister_transactions | lister_transactions | ✅ |
| khelless lia la facture dyal l'eau | latin | payer_facture | lister_factures | ❌ |
| sifet 500 DH l Fatima | latin | faire_virement | faire_virement | ✅ |
| les factures dyali li ma khellesthomch | melange | lister_factures | lister_factures | ✅ |
| chkoun rbe7 lmatch lbare7 ? | latin | (aucun) | (aucun) | ✅ |
| شنو الجو غدا فكازا؟ | arabe | (aucun) | (aucun) | ✅ |
| 3tini recette dyal tajine b l7out | latin | (aucun) | (aucun) | ✅ |
| écris-moi un poème 3la l b7er | melange | (aucun) | (aucun) | ✅ |
| fin kayn a9rab pharmacie ? | latin | (aucun) | (aucun) | ✅ |
