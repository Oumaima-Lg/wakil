# Recherche dans la FAQ : résultats mesurés

Modèle d'embeddings : `bge-m3` · 13 fiches · 38 questions de FAQ et 10 questions qui n'en sont pas · seuil actuel dans `app/faq.py` : 0.60

Généré par `evals/faq/mesurer.py`. **hit@1** : la bonne fiche arrive en premier. **hit@3** : elle est dans les trois premières. Les questions de test sont différentes des questions types écrites dans les fiches.

## Par écriture

| Écriture | hit@1 | hit@3 |
|---|---|---|
| Lettres arabes | 60 % (6/10) | 80 % (8/10) |
| Lettres latines | 71 % (10/14) | 93 % (13/14) |
| Mélange darija et français | 73 % (8/11) | 91 % (10/11) |
| Français | 100 % (3/3) | 100 % (3/3) |
| **Total** | **71 % (27/38)** | **89 % (34/38)** |

## Choix du seuil

Pour chaque seuil : ce que Wakil ferait. Une question de FAQ est **bien servie** si la première fiche est la bonne et dépasse le seuil ; **mal servie** si une mauvaise fiche dépasse le seuil (Wakil cite un texte qui ne répond pas) ; **sans réponse** sinon. Une question hors FAQ ne doit jamais dépasser le seuil.

| Seuil | FAQ bien servie | FAQ mal servie | FAQ sans réponse | Hors FAQ servie à tort |
|---|---|---|---|---|
| 0.40 | 71 % (27/38) | 29 % (11/38) | 0 % (0/38) | 100 % (10/10) |
| 0.45 | 71 % (27/38) | 29 % (11/38) | 0 % (0/38) | 90 % (9/10) |
| 0.50 | 71 % (27/38) | 24 % (9/38) | 5 % (2/38) | 70 % (7/10) |
| 0.55 | 68 % (26/38) | 21 % (8/38) | 11 % (4/38) | 70 % (7/10) |
| 0.60 | 63 % (24/38) | 11 % (4/38) | 26 % (10/38) | 70 % (7/10) |
| 0.65 | 42 % (16/38) | 3 % (1/38) | 55 % (21/38) | 20 % (2/10) |
| 0.70 | 29 % (11/38) | 3 % (1/38) | 68 % (26/38) | 20 % (2/10) |
| 0.75 | 13 % (5/38) | 3 % (1/38) | 84 % (32/38) | 10 % (1/10) |
| 0.80 | 3 % (1/38) | 3 % (1/38) | 95 % (36/38) | 0 % (0/10) |
| 0.85 | 3 % (1/38) | 3 % (1/38) | 95 % (36/38) | 0 % (0/10) |

Meilleur score d'une question hors FAQ : **0.77**. Plus faible score d'une question de FAQ bien classée : **0.55**.

Temps de recherche (vecteur de la question + requête pgvector) : médiane 71 ms, maximum 7927 ms.

## Détail de chaque question

| Question | Écriture | Attendu | 1re fiche (score) | 2e | 3e | |
|---|---|---|---|---|---|---|
| شحال كيتخلص الحساب فالشهر؟ | arabe | frais | plafond (0.58) | frais (0.57) | factures (0.55) | ❌ |
| واش نقدر نصيفط عشرين ألف درهم مرة وحدة؟ | arabe | plafond | plafond (0.63) | beneficiaires (0.52) | frais (0.51) | ✅ |
| الفلوس اللي صيفطت لخويا إمتى غادي توصل؟ | arabe | delai-virement | factures (0.46) | delai-virement (0.45) | donnees (0.43) | ❌ |
| بغيت نزيد صاحبي فالليستة باش نصيفط ليه | arabe | beneficiaires | beneficiaires (0.64) | plafond (0.52) | securite (0.52) | ✅ |
| سرقو ليا البزطام والكارطة كانت فيه | arabe | carte-perdue | carte-perdue (0.73) | contester (0.55) | securite (0.49) | ✅ |
| واحد عيط ليا وطلب الكود اللي جاني فالميساج | arabe | securite | securite (0.62) | carte-perdue (0.58) | beneficiaires (0.56) | ✅ |
| كاينة شي عملية فالحساب ديالي ما عرفتهاش | arabe | contester | contester (0.65) | factures (0.59) | frais (0.56) | ✅ |
| إلا ما كفاش الصولد واش غادي تخلص الفاتورة؟ | arabe | decouvert | factures (0.53) | contester (0.51) | wakil (0.44) | ❌ |
| واش المعلومات ديالي كتمشي لشي بلاصة؟ | arabe | donnees | donnees (0.55) | contester (0.53) | confirmation (0.53) | ✅ |
| واش نقدر نهضر معاك فالليل؟ | arabe | horaires | beneficiaires (0.61) | securite (0.58) | confirmation (0.55) | ❌ |
| wach kaykhlsoni ila sifet l chi bank khra ? | latin | frais | confirmation (0.55) | frais (0.55) | decouvert (0.53) | ❌ |
| ch7al l7ed dyal l virement l wa7ed ? | latin | plafond | delai-virement (0.86) | frais (0.82) | contester (0.61) | ❌ |
| sift lflous l mama, imta twslha ? | latin | delai-virement | delai-virement (0.70) | decouvert (0.61) | securite (0.59) | ✅ |
| kifach nkhelles facture dyal telephone ? | latin | factures | factures (0.86) | contester (0.68) | beneficiaires (0.63) | ✅ |
| 3lach kaytl3 lia had l carte dyal confirmation ? | latin | confirmation | confirmation (0.69) | carte-perdue (0.67) | securite (0.67) | ✅ |
| carte dyali mab9atch 3endi, tal9at lia | latin | carte-perdue | carte-perdue (0.76) | securite (0.71) | contester (0.66) | ✅ |
| wach nsifet lik mot de passe bach tchouf l compte ? | latin | securite | securite (0.64) | wakil (0.62) | factures (0.61) | ✅ |
| ma3endich flous bzaf, wach t9der tkhelles b credit ? | latin | decouvert | decouvert (0.72) | wakil (0.68) | donnees (0.58) | ✅ |
| chno lkhdma li kadirha nta ? | latin | wakil | horaires (0.62) | wakil (0.59) | factures (0.55) | ❌ |
| wach had l'application dyal bss7 wla ghi demo ? | latin | donnees | donnees (0.65) | delai-virement (0.56) | securite (0.55) | ✅ |
| les virements wach payants ? | melange | frais | delai-virement (0.62) | plafond (0.59) | frais (0.58) | ❌ |
| le maximum li n9der nvirer f une seule fois ch7al ? | melange | plafond | plafond (0.62) | frais (0.61) | delai-virement (0.60) | ✅ |
| le virement kaykhd combien de temps ? | melange | delai-virement | delai-virement (0.58) | plafond (0.56) | frais (0.54) | ✅ |
| ajouter un nouveau bénéficiaire, wach possible ? | melange | beneficiaires | beneficiaires (0.79) | plafond (0.53) | wakil (0.52) | ✅ |
| la facture d'électricité, wach t9der tpayiha ? | melange | factures | factures (0.68) | wakil (0.67) | carte-perdue (0.63) | ✅ |
| si je dis non f la confirmation chno kayw9e3 ? | melange | confirmation | confirmation (0.71) | decouvert (0.69) | wakil (0.57) | ✅ |
| j'ai perdu ma carte, chno khassni ndir ? | melange | carte-perdue | carte-perdue (0.70) | securite (0.66) | contester (0.64) | ✅ |
| kayna une opération bizarre f le relevé dyali | melange | contester | contester (0.66) | plafond (0.56) | carte-perdue (0.53) | ✅ |
| le découvert wach autorisé ? | melange | decouvert | donnees (0.48) | decouvert (0.48) | delai-virement (0.48) | ❌ |
| Wakil disponible le weekend ? | melange | horaires | wakil (0.58) | securite (0.54) | factures (0.53) | ❌ |
| bghite nzide benificaire | latin | beneficiaires | plafond (0.55) | beneficiaires (0.53) | contester (0.50) | ❌ |
| chnahiya fonction dyalke ? | latin | wakil | wakil (0.62) | delai-virement (0.51) | factures (0.50) | ✅ |
| quel est ton role ? | francais | wakil | wakil (0.66) | carte-perdue (0.48) | securite (0.47) | ✅ |
| quels sont tes services ? | francais | wakil | wakil (0.72) | horaires (0.54) | securite (0.54) | ✅ |
| 5adamate dyalke ? | latin | wakil | wakil (0.56) | securite (0.50) | horaires (0.50) | ✅ |
| chno howa plafond dyali | latin | plafond | plafond (0.79) | wakil (0.63) | factures (0.55) | ✅ |
| comment ajouter un Bénéficiaire ? | francais | beneficiaires | beneficiaires (0.72) | plafond (0.46) | securite (0.46) | ✅ |
| kifache n payer une factuer ? | melange | factures | factures (0.76) | contester (0.66) | beneficiaires (0.60) | ✅ |
| chhal bqa f compte dyali ? | latin | (hors FAQ) | factures (0.63) | wakil (0.62) | plafond (0.59) | · |
| شنو هوما آخر العمليات ديالي؟ | arabe | (hors FAQ) | wakil (0.62) | contester (0.46) | securite (0.44) | · |
| khelless lia la facture dyal l'eau | latin | (hors FAQ) | factures (0.74) | frais (0.65) | carte-perdue (0.63) | · |
| sifet 500 DH l Fatima | latin | (hors FAQ) | plafond (0.50) | beneficiaires (0.46) | carte-perdue (0.46) | · |
| les factures dyali li ma khellesthomch | melange | (hors FAQ) | factures (0.77) | frais (0.66) | carte-perdue (0.59) | · |
| chkoun rbe7 lmatch lbare7 ? | latin | (hors FAQ) | contester (0.63) | donnees (0.60) | horaires (0.56) | · |
| شنو الجو غدا فكازا؟ | arabe | (hors FAQ) | carte-perdue (0.44) | decouvert (0.44) | frais (0.42) | · |
| 3tini recette dyal tajine b l7out | latin | (hors FAQ) | securite (0.63) | carte-perdue (0.58) | donnees (0.56) | · |
| écris-moi un poème 3la l b7er | melange | (hors FAQ) | securite (0.61) | carte-perdue (0.53) | contester (0.53) | · |
| fin kayn a9rab pharmacie ? | latin | (hors FAQ) | frais (0.49) | wakil (0.49) | decouvert (0.48) | · |
