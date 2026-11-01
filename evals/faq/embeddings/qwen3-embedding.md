# Recherche dans la FAQ : résultats mesurés

Modèle d'embeddings : `qwen3-embedding:0.6b` · 13 fiches · 38 questions de FAQ et 10 questions qui n'en sont pas · seuil actuel dans `app/faq.py` : 0.60

Généré par `evals/faq/mesurer.py`. **hit@1** : la bonne fiche arrive en premier. **hit@3** : elle est dans les trois premières. Les questions de test sont différentes des questions types écrites dans les fiches.

## Par écriture

| Écriture | hit@1 | hit@3 |
|---|---|---|
| Lettres arabes | 30 % (3/10) | 90 % (9/10) |
| Lettres latines | 64 % (9/14) | 93 % (13/14) |
| Mélange darija et français | 64 % (7/11) | 91 % (10/11) |
| Français | 100 % (3/3) | 100 % (3/3) |
| **Total** | **58 % (22/38)** | **92 % (35/38)** |

## Choix du seuil

Pour chaque seuil : ce que Wakil ferait. Une question de FAQ est **bien servie** si la première fiche est la bonne et dépasse le seuil ; **mal servie** si une mauvaise fiche dépasse le seuil (Wakil cite un texte qui ne répond pas) ; **sans réponse** sinon. Une question hors FAQ ne doit jamais dépasser le seuil.

| Seuil | FAQ bien servie | FAQ mal servie | FAQ sans réponse | Hors FAQ servie à tort |
|---|---|---|---|---|
| 0.40 | 58 % (22/38) | 42 % (16/38) | 0 % (0/38) | 100 % (10/10) |
| 0.45 | 58 % (22/38) | 42 % (16/38) | 0 % (0/38) | 100 % (10/10) |
| 0.50 | 58 % (22/38) | 39 % (15/38) | 3 % (1/38) | 90 % (9/10) |
| 0.55 | 58 % (22/38) | 34 % (13/38) | 8 % (3/38) | 80 % (8/10) |
| 0.60 | 53 % (20/38) | 26 % (10/38) | 21 % (8/38) | 70 % (7/10) |
| 0.65 | 47 % (18/38) | 21 % (8/38) | 32 % (12/38) | 40 % (4/10) |
| 0.70 | 32 % (12/38) | 11 % (4/38) | 58 % (22/38) | 40 % (4/10) |
| 0.75 | 21 % (8/38) | 3 % (1/38) | 76 % (29/38) | 30 % (3/10) |
| 0.80 | 11 % (4/38) | 3 % (1/38) | 87 % (33/38) | 20 % (2/10) |
| 0.85 | 3 % (1/38) | 3 % (1/38) | 95 % (36/38) | 0 % (0/10) |

Meilleur score d'une question hors FAQ : **0.84**. Plus faible score d'une question de FAQ bien classée : **0.55**.

Temps de recherche (vecteur de la question + requête pgvector) : médiane 70 ms, maximum 347 ms.

## Détail de chaque question

| Question | Écriture | Attendu | 1re fiche (score) | 2e | 3e | |
|---|---|---|---|---|---|---|
| شحال كيتخلص الحساب فالشهر؟ | arabe | frais | factures (0.61) | frais (0.61) | delai-virement (0.54) | ❌ |
| واش نقدر نصيفط عشرين ألف درهم مرة وحدة؟ | arabe | plafond | plafond (0.59) | beneficiaires (0.52) | frais (0.43) | ✅ |
| الفلوس اللي صيفطت لخويا إمتى غادي توصل؟ | arabe | delai-virement | delai-virement (0.66) | contester (0.53) | decouvert (0.50) | ✅ |
| بغيت نزيد صاحبي فالليستة باش نصيفط ليه | arabe | beneficiaires | beneficiaires (0.61) | plafond (0.55) | decouvert (0.42) | ✅ |
| سرقو ليا البزطام والكارطة كانت فيه | arabe | carte-perdue | contester (0.47) | carte-perdue (0.43) | beneficiaires (0.38) | ❌ |
| واحد عيط ليا وطلب الكود اللي جاني فالميساج | arabe | securite | beneficiaires (0.59) | securite (0.58) | donnees (0.51) | ❌ |
| كاينة شي عملية فالحساب ديالي ما عرفتهاش | arabe | contester | wakil (0.56) | contester (0.56) | securite (0.55) | ❌ |
| إلا ما كفاش الصولد واش غادي تخلص الفاتورة؟ | arabe | decouvert | factures (0.59) | frais (0.48) | decouvert (0.46) | ❌ |
| واش المعلومات ديالي كتمشي لشي بلاصة؟ | arabe | donnees | securite (0.64) | donnees (0.63) | wakil (0.62) | ❌ |
| واش نقدر نهضر معاك فالليل؟ | arabe | horaires | decouvert (0.54) | confirmation (0.53) | delai-virement (0.52) | ❌ |
| wach kaykhlsoni ila sifet l chi bank khra ? | latin | frais | securite (0.67) | delai-virement (0.67) | frais (0.67) | ❌ |
| ch7al l7ed dyal l virement l wa7ed ? | latin | plafond | delai-virement (0.90) | frais (0.84) | plafond (0.78) | ❌ |
| sift lflous l mama, imta twslha ? | latin | delai-virement | delai-virement (0.70) | decouvert (0.62) | wakil (0.59) | ✅ |
| kifach nkhelles facture dyal telephone ? | latin | factures | factures (0.84) | frais (0.72) | securite (0.69) | ✅ |
| 3lach kaytl3 lia had l carte dyal confirmation ? | latin | confirmation | confirmation (0.77) | securite (0.75) | donnees (0.70) | ✅ |
| carte dyali mab9atch 3endi, tal9at lia | latin | carte-perdue | carte-perdue (0.74) | securite (0.69) | wakil (0.64) | ✅ |
| wach nsifet lik mot de passe bach tchouf l compte ? | latin | securite | frais (0.65) | securite (0.63) | delai-virement (0.57) | ❌ |
| ma3endich flous bzaf, wach t9der tkhelles b credit ? | latin | decouvert | decouvert (0.68) | contester (0.63) | plafond (0.62) | ✅ |
| chno lkhdma li kadirha nta ? | latin | wakil | horaires (0.71) | wakil (0.70) | decouvert (0.61) | ❌ |
| wach had l'application dyal bss7 wla ghi demo ? | latin | donnees | donnees (0.72) | delai-virement (0.63) | securite (0.59) | ✅ |
| les virements wach payants ? | melange | frais | plafond (0.74) | delai-virement (0.66) | frais (0.61) | ❌ |
| le maximum li n9der nvirer f une seule fois ch7al ? | melange | plafond | plafond (0.69) | frais (0.64) | wakil (0.60) | ✅ |
| le virement kaykhd combien de temps ? | melange | delai-virement | delai-virement (0.71) | frais (0.68) | plafond (0.63) | ✅ |
| ajouter un nouveau bénéficiaire, wach possible ? | melange | beneficiaires | beneficiaires (0.84) | frais (0.49) | donnees (0.46) | ✅ |
| la facture d'électricité, wach t9der tpayiha ? | melange | factures | frais (0.68) | factures (0.68) | wakil (0.63) | ❌ |
| si je dis non f la confirmation chno kayw9e3 ? | melange | confirmation | confirmation (0.72) | decouvert (0.67) | wakil (0.63) | ✅ |
| j'ai perdu ma carte, chno khassni ndir ? | melange | carte-perdue | securite (0.66) | carte-perdue (0.62) | wakil (0.56) | ❌ |
| kayna une opération bizarre f le relevé dyali | melange | contester | contester (0.70) | wakil (0.66) | donnees (0.65) | ✅ |
| le découvert wach autorisé ? | melange | decouvert | contester (0.53) | donnees (0.51) | securite (0.51) | ❌ |
| Wakil disponible le weekend ? | melange | horaires | horaires (0.55) | wakil (0.54) | factures (0.49) | ✅ |
| bghite nzide benificaire | latin | beneficiaires | plafond (0.73) | contester (0.69) | carte-perdue (0.68) | ❌ |
| chnahiya fonction dyalke ? | latin | wakil | wakil (0.80) | donnees (0.68) | factures (0.67) | ✅ |
| quel est ton role ? | francais | wakil | wakil (0.61) | factures (0.43) | contester (0.42) | ✅ |
| quels sont tes services ? | francais | wakil | wakil (0.68) | factures (0.48) | donnees (0.47) | ✅ |
| 5adamate dyalke ? | latin | wakil | wakil (0.76) | donnees (0.67) | carte-perdue (0.66) | ✅ |
| chno howa plafond dyali | latin | plafond | plafond (0.85) | wakil (0.77) | carte-perdue (0.73) | ✅ |
| comment ajouter un Bénéficiaire ? | francais | beneficiaires | beneficiaires (0.82) | contester (0.52) | wakil (0.51) | ✅ |
| kifache n payer une factuer ? | melange | factures | factures (0.79) | frais (0.73) | contester (0.67) | ✅ |
| chhal bqa f compte dyali ? | latin | (hors FAQ) | wakil (0.78) | donnees (0.70) | frais (0.70) | · |
| شنو هوما آخر العمليات ديالي؟ | arabe | (hors FAQ) | wakil (0.74) | confirmation (0.49) | factures (0.49) | · |
| khelless lia la facture dyal l'eau | latin | (hors FAQ) | factures (0.81) | frais (0.76) | carte-perdue (0.67) | · |
| sifet 500 DH l Fatima | latin | (hors FAQ) | contester (0.64) | carte-perdue (0.61) | delai-virement (0.57) | · |
| les factures dyali li ma khellesthomch | melange | (hors FAQ) | factures (0.84) | frais (0.79) | donnees (0.70) | · |
| chkoun rbe7 lmatch lbare7 ? | latin | (hors FAQ) | contester (0.65) | beneficiaires (0.64) | securite (0.63) | · |
| شنو الجو غدا فكازا؟ | arabe | (hors FAQ) | confirmation (0.50) | decouvert (0.50) | wakil (0.49) | · |
| 3tini recette dyal tajine b l7out | latin | (hors FAQ) | carte-perdue (0.62) | plafond (0.58) | donnees (0.57) | · |
| écris-moi un poème 3la l b7er | melange | (hors FAQ) | carte-perdue (0.50) | wakil (0.49) | beneficiaires (0.48) | · |
| fin kayn a9rab pharmacie ? | latin | (hors FAQ) | contester (0.58) | securite (0.58) | frais (0.57) | · |
