# Recherche dans la FAQ : résultats mesurés

Modèle d'embeddings : `embeddinggemma` · 13 fiches · 38 questions de FAQ et 10 questions qui n'en sont pas · seuil actuel dans `app/faq.py` : 0.60

Généré par `evals/faq/mesurer.py`. **hit@1** : la bonne fiche arrive en premier. **hit@3** : elle est dans les trois premières. Les questions de test sont différentes des questions types écrites dans les fiches.

## Par écriture

| Écriture | hit@1 | hit@3 |
|---|---|---|
| Lettres arabes | 70 % (7/10) | 90 % (9/10) |
| Lettres latines | 64 % (9/14) | 86 % (12/14) |
| Mélange darija et français | 73 % (8/11) | 100 % (11/11) |
| Français | 100 % (3/3) | 100 % (3/3) |
| **Total** | **71 % (27/38)** | **92 % (35/38)** |

## Choix du seuil

Pour chaque seuil : ce que Wakil ferait. Une question de FAQ est **bien servie** si la première fiche est la bonne et dépasse le seuil ; **mal servie** si une mauvaise fiche dépasse le seuil (Wakil cite un texte qui ne répond pas) ; **sans réponse** sinon. Une question hors FAQ ne doit jamais dépasser le seuil.

| Seuil | FAQ bien servie | FAQ mal servie | FAQ sans réponse | Hors FAQ servie à tort |
|---|---|---|---|---|
| 0.40 | 58 % (22/38) | 21 % (8/38) | 21 % (8/38) | 50 % (5/10) |
| 0.45 | 47 % (18/38) | 13 % (5/38) | 39 % (15/38) | 40 % (4/10) |
| 0.50 | 34 % (13/38) | 8 % (3/38) | 58 % (22/38) | 20 % (2/10) |
| 0.55 | 24 % (9/38) | 5 % (2/38) | 71 % (27/38) | 20 % (2/10) |
| 0.60 | 16 % (6/38) | 3 % (1/38) | 82 % (31/38) | 10 % (1/10) |
| 0.65 | 5 % (2/38) | 3 % (1/38) | 92 % (35/38) | 10 % (1/10) |
| 0.70 | 3 % (1/38) | 3 % (1/38) | 95 % (36/38) | 0 % (0/10) |
| 0.75 | 0 % (0/38) | 0 % (0/38) | 100 % (38/38) | 0 % (0/10) |
| 0.80 | 0 % (0/38) | 0 % (0/38) | 100 % (38/38) | 0 % (0/10) |
| 0.85 | 0 % (0/38) | 0 % (0/38) | 100 % (38/38) | 0 % (0/10) |

Meilleur score d'une question hors FAQ : **0.67**. Plus faible score d'une question de FAQ bien classée : **0.30**.

Temps de recherche (vecteur de la question + requête pgvector) : médiane 72 ms, maximum 138 ms.

## Détail de chaque question

| Question | Écriture | Attendu | 1re fiche (score) | 2e | 3e | |
|---|---|---|---|---|---|---|
| شحال كيتخلص الحساب فالشهر؟ | arabe | frais | frais (0.39) | wakil (0.37) | factures (0.37) | ✅ |
| واش نقدر نصيفط عشرين ألف درهم مرة وحدة؟ | arabe | plafond | plafond (0.45) | beneficiaires (0.32) | decouvert (0.29) | ✅ |
| الفلوس اللي صيفطت لخويا إمتى غادي توصل؟ | arabe | delai-virement | securite (0.39) | frais (0.37) | wakil (0.34) | ❌ |
| بغيت نزيد صاحبي فالليستة باش نصيفط ليه | arabe | beneficiaires | beneficiaires (0.47) | plafond (0.38) | decouvert (0.32) | ✅ |
| سرقو ليا البزطام والكارطة كانت فيه | arabe | carte-perdue | carte-perdue (0.36) | beneficiaires (0.28) | contester (0.23) | ✅ |
| واحد عيط ليا وطلب الكود اللي جاني فالميساج | arabe | securite | securite (0.48) | contester (0.33) | horaires (0.32) | ✅ |
| كاينة شي عملية فالحساب ديالي ما عرفتهاش | arabe | contester | frais (0.38) | contester (0.38) | confirmation (0.32) | ❌ |
| إلا ما كفاش الصولد واش غادي تخلص الفاتورة؟ | arabe | decouvert | factures (0.40) | decouvert (0.39) | contester (0.39) | ❌ |
| واش المعلومات ديالي كتمشي لشي بلاصة؟ | arabe | donnees | donnees (0.56) | decouvert (0.40) | frais (0.38) | ✅ |
| واش نقدر نهضر معاك فالليل؟ | arabe | horaires | horaires (0.41) | confirmation (0.39) | decouvert (0.38) | ✅ |
| wach kaykhlsoni ila sifet l chi bank khra ? | latin | frais | securite (0.55) | horaires (0.44) | donnees (0.44) | ❌ |
| ch7al l7ed dyal l virement l wa7ed ? | latin | plafond | delai-virement (0.74) | frais (0.69) | contester (0.59) | ❌ |
| sift lflous l mama, imta twslha ? | latin | delai-virement | delai-virement (0.51) | decouvert (0.41) | horaires (0.39) | ✅ |
| kifach nkhelles facture dyal telephone ? | latin | factures | factures (0.60) | frais (0.51) | donnees (0.31) | ✅ |
| 3lach kaytl3 lia had l carte dyal confirmation ? | latin | confirmation | carte-perdue (0.50) | securite (0.43) | confirmation (0.40) | ❌ |
| carte dyali mab9atch 3endi, tal9at lia | latin | carte-perdue | carte-perdue (0.67) | securite (0.48) | decouvert (0.40) | ✅ |
| wach nsifet lik mot de passe bach tchouf l compte ? | latin | securite | securite (0.52) | beneficiaires (0.45) | wakil (0.44) | ✅ |
| ma3endich flous bzaf, wach t9der tkhelles b credit ? | latin | decouvert | wakil (0.40) | frais (0.40) | decouvert (0.40) | ❌ |
| chno lkhdma li kadirha nta ? | latin | wakil | horaires (0.46) | wakil (0.45) | delai-virement (0.38) | ❌ |
| wach had l'application dyal bss7 wla ghi demo ? | latin | donnees | donnees (0.49) | wakil (0.33) | contester (0.31) | ✅ |
| les virements wach payants ? | melange | frais | plafond (0.55) | delai-virement (0.51) | frais (0.50) | ❌ |
| le maximum li n9der nvirer f une seule fois ch7al ? | melange | plafond | plafond (0.47) | decouvert (0.31) | beneficiaires (0.28) | ✅ |
| le virement kaykhd combien de temps ? | melange | delai-virement | delai-virement (0.51) | frais (0.45) | plafond (0.41) | ✅ |
| ajouter un nouveau bénéficiaire, wach possible ? | melange | beneficiaires | beneficiaires (0.71) | plafond (0.38) | confirmation (0.34) | ✅ |
| la facture d'électricité, wach t9der tpayiha ? | melange | factures | factures (0.60) | frais (0.54) | wakil (0.38) | ✅ |
| si je dis non f la confirmation chno kayw9e3 ? | melange | confirmation | confirmation (0.43) | decouvert (0.40) | wakil (0.37) | ✅ |
| j'ai perdu ma carte, chno khassni ndir ? | melange | carte-perdue | carte-perdue (0.54) | securite (0.51) | wakil (0.33) | ✅ |
| kayna une opération bizarre f le relevé dyali | melange | contester | confirmation (0.43) | contester (0.43) | carte-perdue (0.39) | ❌ |
| le découvert wach autorisé ? | melange | decouvert | confirmation (0.42) | decouvert (0.39) | contester (0.33) | ❌ |
| Wakil disponible le weekend ? | melange | horaires | horaires (0.41) | factures (0.38) | beneficiaires (0.38) | ✅ |
| bghite nzide benificaire | latin | beneficiaires | beneficiaires (0.44) | plafond (0.43) | carte-perdue (0.39) | ✅ |
| chnahiya fonction dyalke ? | latin | wakil | wakil (0.37) | delai-virement (0.31) | plafond (0.31) | ✅ |
| quel est ton role ? | francais | wakil | wakil (0.37) | horaires (0.22) | carte-perdue (0.22) | ✅ |
| quels sont tes services ? | francais | wakil | wakil (0.55) | horaires (0.25) | factures (0.25) | ✅ |
| 5adamate dyalke ? | latin | wakil | wakil (0.30) | donnees (0.30) | delai-virement (0.27) | ✅ |
| chno howa plafond dyali | latin | plafond | plafond (0.63) | wakil (0.40) | carte-perdue (0.34) | ✅ |
| comment ajouter un Bénéficiaire ? | francais | beneficiaires | beneficiaires (0.63) | plafond (0.27) | wakil (0.27) | ✅ |
| kifache n payer une factuer ? | melange | factures | factures (0.63) | frais (0.50) | contester (0.39) | ✅ |
| chhal bqa f compte dyali ? | latin | (hors FAQ) | wakil (0.46) | frais (0.44) | delai-virement (0.38) | · |
| شنو هوما آخر العمليات ديالي؟ | arabe | (hors FAQ) | contester (0.42) | confirmation (0.34) | carte-perdue (0.33) | · |
| khelless lia la facture dyal l'eau | latin | (hors FAQ) | factures (0.59) | frais (0.49) | carte-perdue (0.34) | · |
| sifet 500 DH l Fatima | latin | (hors FAQ) | beneficiaires (0.30) | horaires (0.27) | securite (0.27) | · |
| les factures dyali li ma khellesthomch | melange | (hors FAQ) | factures (0.67) | frais (0.55) | carte-perdue (0.35) | · |
| chkoun rbe7 lmatch lbare7 ? | latin | (hors FAQ) | contester (0.47) | horaires (0.44) | delai-virement (0.42) | · |
| شنو الجو غدا فكازا؟ | arabe | (hors FAQ) | frais (0.18) | plafond (0.18) | factures (0.17) | · |
| 3tini recette dyal tajine b l7out | latin | (hors FAQ) | carte-perdue (0.34) | beneficiaires (0.32) | plafond (0.32) | · |
| écris-moi un poème 3la l b7er | melange | (hors FAQ) | carte-perdue (0.38) | contester (0.36) | beneficiaires (0.31) | · |
| fin kayn a9rab pharmacie ? | latin | (hors FAQ) | decouvert (0.35) | frais (0.32) | beneficiaires (0.32) | · |
