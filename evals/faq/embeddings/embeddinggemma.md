# Recherche dans la FAQ : résultats mesurés

Modèle d'embeddings : `embeddinggemma` · 13 fiches · 38 questions de FAQ et 10 questions qui n'en sont pas · seuil actuel dans `app/faq.py` : 0.60

Généré par `evals/faq/mesurer.py`. **hit@1** : la bonne fiche arrive en premier. **hit@3** : elle est dans les trois premières. Les questions de test sont différentes des questions types écrites dans les fiches.

## Par écriture

| Écriture | hit@1 | hit@3 |
|---|---|---|
| Lettres arabes | 50 % (5/10) | 90 % (9/10) |
| Lettres latines | 64 % (9/14) | 86 % (12/14) |
| Mélange darija et français | 82 % (9/11) | 100 % (11/11) |
| Français | 100 % (3/3) | 100 % (3/3) |
| **Total** | **68 % (26/38)** | **92 % (35/38)** |

## Choix du seuil

Pour chaque seuil : ce que Wakil ferait. Une question de FAQ est **bien servie** si la première fiche est la bonne et dépasse le seuil ; **mal servie** si une mauvaise fiche dépasse le seuil (Wakil cite un texte qui ne répond pas) ; **sans réponse** sinon. Une question hors FAQ ne doit jamais dépasser le seuil.

| Seuil | FAQ bien servie | FAQ mal servie | FAQ sans réponse | Hors FAQ servie à tort |
|---|---|---|---|---|
| 0.40 | 68 % (26/38) | 32 % (12/38) | 0 % (0/38) | 100 % (10/10) |
| 0.45 | 66 % (25/38) | 32 % (12/38) | 3 % (1/38) | 70 % (7/10) |
| 0.50 | 63 % (24/38) | 32 % (12/38) | 5 % (2/38) | 60 % (6/10) |
| 0.55 | 58 % (22/38) | 29 % (11/38) | 13 % (5/38) | 60 % (6/10) |
| 0.60 | 55 % (21/38) | 24 % (9/38) | 21 % (8/38) | 50 % (5/10) |
| 0.65 | 47 % (18/38) | 16 % (6/38) | 37 % (14/38) | 40 % (4/10) |
| 0.70 | 37 % (14/38) | 13 % (5/38) | 50 % (19/38) | 30 % (3/10) |
| 0.75 | 26 % (10/38) | 8 % (3/38) | 66 % (25/38) | 20 % (2/10) |
| 0.80 | 8 % (3/38) | 3 % (1/38) | 89 % (34/38) | 10 % (1/10) |
| 0.85 | 0 % (0/38) | 3 % (1/38) | 97 % (37/38) | 0 % (0/10) |

Meilleur score d'une question hors FAQ : **0.81**. Plus faible score d'une question de FAQ bien classée : **0.41**.

Temps de recherche (vecteur de la question + requête pgvector) : médiane 119 ms, maximum 16711 ms.

## Détail de chaque question

| Question | Écriture | Attendu | 1re fiche (score) | 2e | 3e | |
|---|---|---|---|---|---|---|
| شحال كيتخلص الحساب فالشهر؟ | arabe | frais | wakil (0.63) | frais (0.58) | factures (0.58) | ❌ |
| واش نقدر نصيفط عشرين ألف درهم مرة وحدة؟ | arabe | plafond | plafond (0.60) | factures (0.53) | frais (0.51) | ✅ |
| الفلوس اللي صيفطت لخويا إمتى غادي توصل؟ | arabe | delai-virement | factures (0.62) | delai-virement (0.57) | decouvert (0.54) | ❌ |
| بغيت نزيد صاحبي فالليستة باش نصيفط ليه | arabe | beneficiaires | beneficiaires (0.79) | plafond (0.55) | decouvert (0.53) | ✅ |
| سرقو ليا البزطام والكارطة كانت فيه | arabe | carte-perdue | carte-perdue (0.41) | contester (0.41) | horaires (0.38) | ✅ |
| واحد عيط ليا وطلب الكود اللي جاني فالميساج | arabe | securite | securite (0.53) | contester (0.45) | horaires (0.45) | ✅ |
| كاينة شي عملية فالحساب ديالي ما عرفتهاش | arabe | contester | factures (0.59) | wakil (0.56) | decouvert (0.54) | ❌ |
| إلا ما كفاش الصولد واش غادي تخلص الفاتورة؟ | arabe | decouvert | factures (0.59) | decouvert (0.52) | beneficiaires (0.52) | ❌ |
| واش المعلومات ديالي كتمشي لشي بلاصة؟ | arabe | donnees | donnees (0.75) | confirmation (0.61) | wakil (0.60) | ✅ |
| واش نقدر نهضر معاك فالليل؟ | arabe | horaires | confirmation (0.70) | horaires (0.62) | wakil (0.62) | ❌ |
| wach kaykhlsoni ila sifet l chi bank khra ? | latin | frais | horaires (0.77) | donnees (0.74) | wakil (0.69) | ❌ |
| ch7al l7ed dyal l virement l wa7ed ? | latin | plafond | delai-virement (0.89) | frais (0.87) | horaires (0.72) | ❌ |
| sift lflous l mama, imta twslha ? | latin | delai-virement | delai-virement (0.69) | decouvert (0.68) | confirmation (0.68) | ✅ |
| kifach nkhelles facture dyal telephone ? | latin | factures | factures (0.83) | frais (0.66) | confirmation (0.59) | ✅ |
| 3lach kaytl3 lia had l carte dyal confirmation ? | latin | confirmation | carte-perdue (0.71) | securite (0.64) | confirmation (0.62) | ❌ |
| carte dyali mab9atch 3endi, tal9at lia | latin | carte-perdue | carte-perdue (0.80) | decouvert (0.57) | securite (0.54) | ✅ |
| wach nsifet lik mot de passe bach tchouf l compte ? | latin | securite | securite (0.73) | confirmation (0.67) | wakil (0.67) | ✅ |
| ma3endich flous bzaf, wach t9der tkhelles b credit ? | latin | decouvert | factures (0.62) | decouvert (0.61) | wakil (0.60) | ❌ |
| chno lkhdma li kadirha nta ? | latin | wakil | horaires (0.77) | wakil (0.74) | confirmation (0.72) | ❌ |
| wach had l'application dyal bss7 wla ghi demo ? | latin | donnees | donnees (0.68) | horaires (0.62) | wakil (0.56) | ✅ |
| les virements wach payants ? | melange | frais | delai-virement (0.72) | plafond (0.70) | frais (0.69) | ❌ |
| le maximum li n9der nvirer f une seule fois ch7al ? | melange | plafond | plafond (0.76) | decouvert (0.60) | delai-virement (0.59) | ✅ |
| le virement kaykhd combien de temps ? | melange | delai-virement | delai-virement (0.75) | frais (0.73) | contester (0.65) | ✅ |
| ajouter un nouveau bénéficiaire, wach possible ? | melange | beneficiaires | beneficiaires (0.78) | frais (0.50) | plafond (0.49) | ✅ |
| la facture d'électricité, wach t9der tpayiha ? | melange | factures | factures (0.76) | frais (0.63) | decouvert (0.63) | ✅ |
| si je dis non f la confirmation chno kayw9e3 ? | melange | confirmation | confirmation (0.67) | decouvert (0.62) | wakil (0.53) | ✅ |
| j'ai perdu ma carte, chno khassni ndir ? | melange | carte-perdue | carte-perdue (0.74) | securite (0.61) | confirmation (0.56) | ✅ |
| kayna une opération bizarre f le relevé dyali | melange | contester | contester (0.55) | confirmation (0.51) | wakil (0.49) | ✅ |
| le découvert wach autorisé ? | melange | decouvert | wakil (0.52) | horaires (0.52) | decouvert (0.52) | ❌ |
| Wakil disponible le weekend ? | melange | horaires | horaires (0.50) | securite (0.47) | decouvert (0.45) | ✅ |
| bghite nzide benificaire | latin | beneficiaires | beneficiaires (0.63) | plafond (0.51) | decouvert (0.49) | ✅ |
| chnahiya fonction dyalke ? | latin | wakil | wakil (0.59) | confirmation (0.56) | decouvert (0.56) | ✅ |
| quel est ton role ? | francais | wakil | wakil (0.62) | horaires (0.51) | confirmation (0.49) | ✅ |
| quels sont tes services ? | francais | wakil | wakil (0.71) | horaires (0.45) | factures (0.44) | ✅ |
| 5adamate dyalke ? | latin | wakil | wakil (0.69) | horaires (0.63) | confirmation (0.63) | ✅ |
| chno howa plafond dyali | latin | plafond | plafond (0.81) | wakil (0.58) | decouvert (0.51) | ✅ |
| comment ajouter un Bénéficiaire ? | francais | beneficiaires | beneficiaires (0.73) | frais (0.35) | factures (0.35) | ✅ |
| kifache n payer une factuer ? | melange | factures | factures (0.85) | frais (0.65) | decouvert (0.55) | ✅ |
| chhal bqa f compte dyali ? | latin | (hors FAQ) | wakil (0.79) | frais (0.70) | delai-virement (0.66) | · |
| شنو هوما آخر العمليات ديالي؟ | arabe | (hors FAQ) | confirmation (0.58) | wakil (0.55) | delai-virement (0.53) | · |
| khelless lia la facture dyal l'eau | latin | (hors FAQ) | factures (0.72) | frais (0.54) | wakil (0.50) | · |
| sifet 500 DH l Fatima | latin | (hors FAQ) | plafond (0.44) | factures (0.41) | delai-virement (0.40) | · |
| les factures dyali li ma khellesthomch | melange | (hors FAQ) | factures (0.81) | frais (0.63) | wakil (0.55) | · |
| chkoun rbe7 lmatch lbare7 ? | latin | (hors FAQ) | horaires (0.69) | decouvert (0.64) | wakil (0.59) | · |
| شنو الجو غدا فكازا؟ | arabe | (hors FAQ) | decouvert (0.49) | delai-virement (0.47) | confirmation (0.46) | · |
| 3tini recette dyal tajine b l7out | latin | (hors FAQ) | carte-perdue (0.42) | contester (0.41) | decouvert (0.41) | · |
| écris-moi un poème 3la l b7er | melange | (hors FAQ) | decouvert (0.43) | wakil (0.42) | carte-perdue (0.42) | · |
| fin kayn a9rab pharmacie ? | latin | (hors FAQ) | decouvert (0.62) | confirmation (0.61) | delai-virement (0.60) | · |
