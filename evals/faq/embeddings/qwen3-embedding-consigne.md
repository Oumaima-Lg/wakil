# Recherche dans la FAQ : résultats mesurés

Modèle d'embeddings : `qwen3-embedding:0.6b` · 13 fiches · 38 questions de FAQ et 10 questions qui n'en sont pas · seuil actuel dans `app/faq.py` : 0.60

Généré par `evals/faq/mesurer.py`. **hit@1** : la bonne fiche arrive en premier. **hit@3** : elle est dans les trois premières. Les questions de test sont différentes des questions types écrites dans les fiches.

## Par écriture

| Écriture | hit@1 | hit@3 |
|---|---|---|
| Lettres arabes | 60 % (6/10) | 80 % (8/10) |
| Lettres latines | 64 % (9/14) | 100 % (14/14) |
| Mélange darija et français | 73 % (8/11) | 100 % (11/11) |
| Français | 100 % (3/3) | 100 % (3/3) |
| **Total** | **68 % (26/38)** | **95 % (36/38)** |

## Choix du seuil

Pour chaque seuil : ce que Wakil ferait. Une question de FAQ est **bien servie** si la première fiche est la bonne et dépasse le seuil ; **mal servie** si une mauvaise fiche dépasse le seuil (Wakil cite un texte qui ne répond pas) ; **sans réponse** sinon. Une question hors FAQ ne doit jamais dépasser le seuil.

| Seuil | FAQ bien servie | FAQ mal servie | FAQ sans réponse | Hors FAQ servie à tort |
|---|---|---|---|---|
| 0.40 | 68 % (26/38) | 32 % (12/38) | 0 % (0/38) | 100 % (10/10) |
| 0.45 | 68 % (26/38) | 29 % (11/38) | 3 % (1/38) | 80 % (8/10) |
| 0.50 | 63 % (24/38) | 29 % (11/38) | 8 % (3/38) | 50 % (5/10) |
| 0.55 | 63 % (24/38) | 26 % (10/38) | 11 % (4/38) | 40 % (4/10) |
| 0.60 | 37 % (14/38) | 21 % (8/38) | 42 % (16/38) | 40 % (4/10) |
| 0.65 | 24 % (9/38) | 5 % (2/38) | 71 % (27/38) | 40 % (4/10) |
| 0.70 | 13 % (5/38) | 3 % (1/38) | 84 % (32/38) | 30 % (3/10) |
| 0.75 | 5 % (2/38) | 3 % (1/38) | 92 % (35/38) | 0 % (0/10) |
| 0.80 | 0 % (0/38) | 0 % (0/38) | 100 % (38/38) | 0 % (0/10) |
| 0.85 | 0 % (0/38) | 0 % (0/38) | 100 % (38/38) | 0 % (0/10) |

Meilleur score d'une question hors FAQ : **0.72**. Plus faible score d'une question de FAQ bien classée : **0.46**.

Temps de recherche (vecteur de la question + requête pgvector) : médiane 92 ms, maximum 10532 ms.

## Détail de chaque question

| Question | Écriture | Attendu | 1re fiche (score) | 2e | 3e | |
|---|---|---|---|---|---|---|
| شحال كيتخلص الحساب فالشهر؟ | arabe | frais | frais (0.56) | factures (0.54) | delai-virement (0.50) | ✅ |
| واش نقدر نصيفط عشرين ألف درهم مرة وحدة؟ | arabe | plafond | plafond (0.60) | beneficiaires (0.55) | delai-virement (0.48) | ✅ |
| الفلوس اللي صيفطت لخويا إمتى غادي توصل؟ | arabe | delai-virement | delai-virement (0.56) | decouvert (0.51) | confirmation (0.46) | ✅ |
| بغيت نزيد صاحبي فالليستة باش نصيفط ليه | arabe | beneficiaires | beneficiaires (0.63) | plafond (0.53) | securite (0.45) | ✅ |
| سرقو ليا البزطام والكارطة كانت فيه | arabe | carte-perdue | contester (0.44) | carte-perdue (0.41) | beneficiaires (0.39) | ❌ |
| واحد عيط ليا وطلب الكود اللي جاني فالميساج | arabe | securite | securite (0.58) | beneficiaires (0.55) | donnees (0.52) | ✅ |
| كاينة شي عملية فالحساب ديالي ما عرفتهاش | arabe | contester | delai-virement (0.62) | wakil (0.60) | factures (0.57) | ❌ |
| إلا ما كفاش الصولد واش غادي تخلص الفاتورة؟ | arabe | decouvert | factures (0.60) | frais (0.52) | plafond (0.44) | ❌ |
| واش المعلومات ديالي كتمشي لشي بلاصة؟ | arabe | donnees | donnees (0.58) | wakil (0.57) | securite (0.55) | ✅ |
| واش نقدر نهضر معاك فالليل؟ | arabe | horaires | decouvert (0.51) | horaires (0.49) | confirmation (0.49) | ❌ |
| wach kaykhlsoni ila sifet l chi bank khra ? | latin | frais | securite (0.61) | frais (0.59) | donnees (0.59) | ❌ |
| ch7al l7ed dyal l virement l wa7ed ? | latin | plafond | delai-virement (0.78) | frais (0.75) | plafond (0.67) | ❌ |
| sift lflous l mama, imta twslha ? | latin | delai-virement | delai-virement (0.58) | decouvert (0.55) | securite (0.50) | ✅ |
| kifach nkhelles facture dyal telephone ? | latin | factures | factures (0.74) | frais (0.62) | securite (0.56) | ✅ |
| 3lach kaytl3 lia had l carte dyal confirmation ? | latin | confirmation | securite (0.70) | confirmation (0.63) | carte-perdue (0.60) | ❌ |
| carte dyali mab9atch 3endi, tal9at lia | latin | carte-perdue | securite (0.65) | carte-perdue (0.64) | wakil (0.58) | ❌ |
| wach nsifet lik mot de passe bach tchouf l compte ? | latin | securite | securite (0.57) | frais (0.55) | delai-virement (0.53) | ✅ |
| ma3endich flous bzaf, wach t9der tkhelles b credit ? | latin | decouvert | decouvert (0.60) | frais (0.57) | confirmation (0.55) | ✅ |
| chno lkhdma li kadirha nta ? | latin | wakil | horaires (0.58) | wakil (0.55) | contester (0.55) | ❌ |
| wach had l'application dyal bss7 wla ghi demo ? | latin | donnees | donnees (0.61) | delai-virement (0.54) | wakil (0.51) | ✅ |
| les virements wach payants ? | melange | frais | plafond (0.59) | frais (0.59) | delai-virement (0.57) | ❌ |
| le maximum li n9der nvirer f une seule fois ch7al ? | melange | plafond | plafond (0.67) | frais (0.64) | securite (0.54) | ✅ |
| le virement kaykhd combien de temps ? | melange | delai-virement | frais (0.63) | delai-virement (0.62) | plafond (0.57) | ❌ |
| ajouter un nouveau bénéficiaire, wach possible ? | melange | beneficiaires | beneficiaires (0.79) | wakil (0.49) | contester (0.45) | ✅ |
| la facture d'électricité, wach t9der tpayiha ? | melange | factures | factures (0.66) | frais (0.62) | wakil (0.55) | ✅ |
| si je dis non f la confirmation chno kayw9e3 ? | melange | confirmation | confirmation (0.69) | frais (0.57) | carte-perdue (0.55) | ✅ |
| j'ai perdu ma carte, chno khassni ndir ? | melange | carte-perdue | securite (0.60) | carte-perdue (0.58) | frais (0.48) | ❌ |
| kayna une opération bizarre f le relevé dyali | melange | contester | contester (0.60) | donnees (0.60) | wakil (0.57) | ✅ |
| le découvert wach autorisé ? | melange | decouvert | decouvert (0.61) | confirmation (0.57) | delai-virement (0.52) | ✅ |
| Wakil disponible le weekend ? | melange | horaires | horaires (0.46) | wakil (0.44) | securite (0.39) | ✅ |
| bghite nzide benificaire | latin | beneficiaires | beneficiaires (0.58) | plafond (0.49) | carte-perdue (0.49) | ✅ |
| chnahiya fonction dyalke ? | latin | wakil | wakil (0.68) | donnees (0.57) | delai-virement (0.55) | ✅ |
| quel est ton role ? | francais | wakil | wakil (0.46) | contester (0.43) | factures (0.41) | ✅ |
| quels sont tes services ? | francais | wakil | wakil (0.57) | horaires (0.45) | contester (0.45) | ✅ |
| 5adamate dyalke ? | latin | wakil | wakil (0.58) | plafond (0.56) | donnees (0.52) | ✅ |
| chno howa plafond dyali | latin | plafond | plafond (0.73) | wakil (0.57) | carte-perdue (0.54) | ✅ |
| comment ajouter un Bénéficiaire ? | francais | beneficiaires | beneficiaires (0.76) | wakil (0.43) | contester (0.39) | ✅ |
| kifache n payer une factuer ? | melange | factures | factures (0.70) | frais (0.67) | contester (0.51) | ✅ |
| chhal bqa f compte dyali ? | latin | (hors FAQ) | wakil (0.71) | delai-virement (0.65) | frais (0.63) | · |
| شنو هوما آخر العمليات ديالي؟ | arabe | (hors FAQ) | wakil (0.69) | securite (0.48) | delai-virement (0.47) | · |
| khelless lia la facture dyal l'eau | latin | (hors FAQ) | factures (0.70) | frais (0.64) | donnees (0.52) | · |
| sifet 500 DH l Fatima | latin | (hors FAQ) | carte-perdue (0.48) | frais (0.44) | contester (0.44) | · |
| les factures dyali li ma khellesthomch | melange | (hors FAQ) | factures (0.72) | frais (0.65) | donnees (0.55) | · |
| chkoun rbe7 lmatch lbare7 ? | latin | (hors FAQ) | beneficiaires (0.54) | contester (0.53) | securite (0.53) | · |
| شنو الجو غدا فكازا؟ | arabe | (hors FAQ) | decouvert (0.47) | confirmation (0.45) | factures (0.43) | · |
| 3tini recette dyal tajine b l7out | latin | (hors FAQ) | donnees (0.49) | carte-perdue (0.48) | wakil (0.47) | · |
| écris-moi un poème 3la l b7er | melange | (hors FAQ) | beneficiaires (0.41) | decouvert (0.40) | carte-perdue (0.38) | · |
| fin kayn a9rab pharmacie ? | latin | (hors FAQ) | securite (0.43) | frais (0.43) | contester (0.42) | · |
