# Conversations annotées à la main

Avant de construire le benchmark (étape S4), on annote au moins 30 vraies conversations avec Wakil pour
découvrir les familles d'erreurs. Chaque message est jugé de façon binaire : ✅ réussi ou ❌ raté.

**Écriture** : `arabe`, `latin` (arabizi), `mélange` (darija + français), `français`.

**Familles d'erreurs repérées** :

| Famille | Description |
|---|---|
| `politesse` | Un remerciement ou un accusé de réception (« mzyan », « très bien ») traité comme une demande ou du hors-sujet |
| `suite` | Le message n'a de sens qu'avec les messages précédents (Wakil n'a pas encore de mémoire) |
| `pas-encore-disponible` | Une opération prévue plus tard (virement, paiement : étape S3) |
| `composee` | Deux demandes en une (« bghit n5less l'Internet, wach solde kafini ? ») |
| `refus-trompeur` | Le message de refus laisse croire que la demande est hors sujet alors qu'elle concerne la banque |
| `paiement-vs-liste` | Le client demande de payer, le LLM se contente de lister les factures |
| `operation-multiple` | Plusieurs opérations en une (« khelless kolchi ») : Wakil ne sait en faire qu'une par carte de confirmation |
| `parametre-faux` | Le bon outil, avec un mauvais paramètre (le client désigne la facture par son montant, le LLM choisit l'eau) |
| `faq-mal-routee` | Une demande sur le compte envoyée à la FAQ, ou une question de FAQ envoyée ailleurs |
| `faq-mal-servie` | La recherche cite une fiche qui ne répond pas, ou ne trouve rien au-dessus du seuil (0,60) |
| `donnee-manquante` | Le client demande une donnée de son compte qu'aucun outil ne donne (la valeur de son plafond) |
| `chiffre-arabizi` | Hypothèse : le LLM comprend mieux « khelless » que « 5lse » (le chiffre 5 pour خ), et pas « ka3e » (tout) |
| `nombre-non-supporte` | Le client demande un nombre précis d'éléments (« les 3 dernières opérations ») : l'outil en renvoie toujours 5 |

---

## Conversation 1

- **Date** : 18/10/2026 · **Client** : Salma (id 1) · **Modèle** : qwen3:4b-instruct
- **Version de Wakil** : commit `babfa1e` (avant la gestion de la politesse et le nouveau message de refus)
- **Bilan** : 5 ✅ / 7 ❌ sur 12 messages

| # | Message | Écriture | Attendu | Obtenu | Résultat | Famille |
|---|---|---|---|---|---|---|
| 1 | slm | latin | salutation, sans outil | salutation | ✅ | |
| 2 | ch7al b9a f solde dyali | mélange | `consulter_solde` | `consulter_solde` | ✅ | |
| 3 | o les factures ? | mélange | `lister_factures` | `lister_factures` | ✅ | réussi grâce au mot « factures », pas grâce à la mémoire |
| 4 | chno homa les transactions li drte ana | mélange | `lister_transactions` | `lister_transactions` | ✅ | |
| 5 | c'est tout ? | français | `lister_transactions` (plus de lignes) | refus | ❌ | `suite` |
| 6 | tres bien | français | politesse | refus | ❌ | `politesse` |
| 7 | bghite ndire virement | mélange | `faire_virement`, puis demander bénéficiaire et montant | refus « ana ghir l'assistant… » | ❌ | `pas-encore-disponible`, `refus-trompeur` |
| 8 | mzyan | latin | politesse | refus | ❌ | `politesse` |
| 9 | mzn | latin | politesse | refus | ❌ | `politesse` |
| 10 | chnihoma les factures dyali | mélange | `lister_factures` | `lister_factures` | ✅ | |
| 11 | bghite n5lsse Internet, wache solde kafini ? | mélange | `payer_facture` (Internet) + vérification du solde | `lister_factures` | ❌ | `pas-encore-disponible`, `composee` |
| 12 | oui 3rfte mais bghite n5lsse l'Internet, t9dre t9oliya wache solde li 3ndi fl compte kafini bache n5lse la facture dyali ? | mélange | `payer_facture` (Internet) + vérification du solde | `lister_factures` | ❌ | `suite`, `pas-encore-disponible`, `composee` |

**Corrigé depuis** (rejoué sur le vrai agent) : les messages 6, 8 et 9 reçoivent maintenant « Bla jmil ! Ila bghiti chi
haja okhra, ana hna. » sans appeler le LLM ; le message 7 reçoit un refus neutre qui ne prétend plus que le virement
est hors sujet. Restent ouverts : `suite` (mémoire, S2 morceau 5), `pas-encore-disponible` et `composee` (S3).

---

## Conversation 2

- **Date** : 29/10/2026 · **Cliente** : Salma (id 1) · **Testée par** : Oumaima · **Modèles** : `qwen3:4b-instruct` (choix de l'outil), `bge-m3` (FAQ)
- **Version de Wakil** : après le commit `82642f8`, avec le service `rag-faq` (prompt système corrigé, historique relu au format des appels d'outils)
- **Bilan** : 10 ✅ / 20 ❌ sur 30 messages. Les deux paiements demandés clairement passent, avec carte et « oui » ; presque tout le reste échoue sur le choix de l'outil.

| # | Message | Écriture | Attendu | Obtenu | Résultat | Famille |
|---|---|---|---|---|---|---|
| 1 | salam | latin | salutation, sans outil | salutation | ✅ | |
| 3 | kidyre lbsse 3like ? | latin | politesse (« ça va ? ») | refus | ❌ | `politesse` |
| 5 | ch7ale 3ndi f solde ? | latin | `consulter_solde` | `consulter_solde` | ✅ | |
| 7 | chno homa les derniers transactions ? | mélange | `lister_transactions` | `lister_transactions` | ✅ | |
| 9 | sf hir hadchi ? | latin | `lister_transactions` (la suite) | `lister_factures` | ❌ | `suite` |
| 11 | sf ? | latin | politesse | FAQ, rien trouvé (0,51) | ❌ | `politesse` |
| 13 | t9dre t5lsse liya chi facture ? | latin | `payer_facture`, puis « laquelle ? » | `lister_factures` | ❌ | `paiement-vs-liste` |
| 15 | t9dre t5lse liya facture dyal do | latin | `payer_facture` (eau et électricité : « do » = ضو) | `lister_factures` | ❌ | `paiement-vs-liste` |
| 17 | 5lse liya facture dyal lma o do | latin | `payer_facture` (eau et électricité : un seul fournisseur) | `lister_factures` | ❌ | `paiement-vs-liste` |
| 19 | iwa 5lshome kamline | latin | les deux factures, une carte à la fois | `consulter_solde` | ❌ | `operation-multiple`, `suite` |
| 21 | wa 9lte like 5lsse liya kolchi (tous les factures). tu peux me payer tous les factures ? | mélange | idem | refus | ❌ | `operation-multiple` |
| 23 | tu peux me payer tous les factures ? | français | idem | `lister_factures` | ❌ | `operation-multiple` |
| 25 | 5lse liya la facture dyal eau | mélange | `payer_facture` (eau) → carte | carte, 312 DH | ✅ | |
| 27 | oui | latin | confirmation | payée, solde 2 038 DH | ✅ | |
| 29 | mzyne | latin | politesse | refus | ❌ | `politesse` (orthographe absente de la liste) |
| 31 | dba ch7ale b9a liya fl les factures li mzl mt5lsso | mélange | `lister_factures` | `lister_factures` | ✅ | |
| 33 | 5lso | latin | `payer_facture` (Internet, la seule restante) | FAQ, rien trouvé (0,44) | ❌ | `suite`, `faq-mal-routee` |
| 35 | 9lte like 5lsse liya les factures restantes | mélange | `payer_facture` (Internet) | `lister_factures` | ❌ | `paiement-vs-liste` |
| 37 | iwa 5lshome | latin | `payer_facture` (Internet) | `lister_transactions` | ❌ | `suite` |
| 39 | wa la, 9tlike 5lsse facture dyal 249dh | latin | `payer_facture` (Internet, 249 DH) | `payer_facture` (eau) → « ma 3ndek hta facture dyal l'eau » | ❌ | `parametre-faux` |
| 41 | dyal 249dh | latin | idem | `lister_factures` | ❌ | `suite`, `parametre-faux` |
| 43 | 5lse dyal wifi | latin | `payer_facture` (internet) → carte | carte, 249 DH | ✅ | « wifi » bien compris |
| 45 | Oui | latin | confirmation | payée, solde 1 789 DH | ✅ | |
| 47 | machi mochkile | latin | politesse | FAQ, rien trouvé (0,53) | ❌ | `politesse` |
| 49 | chno howa dwre dyalke ? o chanhowa Plafond de virement dyal compte dyali? | mélange | FAQ « Ce que Wakil sait faire » + la valeur du plafond | seulement la première fiche | ❌ | `composee`, `donnee-manquante` |
| 51 | mjwbtiche 3la so2ale tani : chanhowa Plafond de virement dyal ? | mélange | la valeur du plafond (10 000 DH) | FAQ, rien trouvé (0,57) | ❌ | `donnee-manquante`, `faq-mal-servie` |
| 53 | chna howa Plafond de virement dyal ? | mélange | idem | FAQ, rien trouvé (0,60, juste sous le seuil) | ❌ | `donnee-manquante`, `faq-mal-servie` |
| 55 | Quel est mon Plafond de virement ? | français | la valeur du plafond (10 000 DH) | fiche « Plafond de virement » (dit où le voir, pas la valeur) | ❌ | `donnee-manquante` |
| 57 | n9dre nzide les benificaire fl compte dyali ? | mélange | fiche « Bénéficiaires » | fiche « Ce que Wakil sait faire » (dit aussi « ni ajouter un bénéficiaire ») | ✅ | fiche voisine, réponse juste |
| 59 | chno homa les factures dyali ? | mélange | `lister_factures` | « Ma 3ndek hta facture » | ✅ | |

## Conversation 3

- **Date** : 29/10/2026 · **Cliente** : Salma (id 1) · **Testée par** : Oumaima · **Version** : la même que la conversation 2
- **Bilan** : 5 ✅ / 1 ❌ sur 6 messages. Les virements marchent bien, y compris une suite comprise grâce à l'historique.

| # | Message | Écriture | Attendu | Obtenu | Résultat | Famille |
|---|---|---|---|---|---|---|
| 1 | bghite ndire virement l sa7bi | latin | `faire_virement`, puis « à quel bénéficiaire ? » | FAQ « Une opération que je ne reconnais pas » (0,76) | ❌ | `faq-mal-routee`, `faq-mal-servie` |
| 3 | sifti liya 150 f fatima | latin | `faire_virement` (Fatima, 150) → carte | carte, 150 DH à Fatima Lahlou | ✅ | |
| 5 | Oui | latin | confirmation | viré, solde 1 639 DH | ✅ | |
| 7 | bghite 3wtani ndir virement ms had lmra b 200dh | latin | `faire_virement` (Fatima, 200 : la même) | carte, 200 DH à Fatima Lahlou | ✅ | suite comprise |
| 9 | Oui | latin | confirmation | viré, solde 1 439 DH | ✅ | |
| 11 | bghite ndire virement l Ahmed | latin | « Ahmed n'est pas un bénéficiaire » | « Ma l9itch « Ahmed » f les bénéficiaires dyalek. » | ✅ | |

**Ce que montrent les conversations 2 et 3** (à comparer au benchmark, sans correctif au cas par cas) :

- **Ce qui marche** : les opérations demandées clairement (« 5lse liya la facture dyal eau », « 5lse dyal wifi », « sifti liya 150 f fatima »), la confirmation (4 sur 4), la suite d'un virement (« ms had lmra b 200dh ») et le refus d'un bénéficiaire inconnu.
- **Le maillon faible reste le choix de l'outil** : `paiement-vs-liste` (5 fois), `suite` (6 fois), `politesse` (4 fois).
- **Trois vrais manques du produit, pas du LLM** :
  - aucun outil ne donne la **valeur du plafond** du compte (`donnee-manquante`) ;
  - Wakil ne sait pas répondre « une facture à la fois » à « khelless kolchi » (`operation-multiple`) ;
  - on ne peut pas désigner une facture **par son montant** (`parametre-faux`).

## Conversation 4

- **Date** : 29/10/2026 · **Cliente** : Salma (id 1) · **Testée par** : Oumaima · **Version** : avec le morceau 15 (`consulter_plafond`, fournisseur `toutes`, `montant` facultatif)
- **Bilan** : 6 ✅ / 15 ❌ sur 21 messages.

| # | Message | Écriture | Attendu | Obtenu | Résultat | Famille |
|---|---|---|---|---|---|---|
| 1 | chno homa les factures li 3ndi | latin | `lister_factures` | `lister_factures` | ✅ | |
| 3 | 5lse liya ka3e les factures | mélange | `payer_facture` (toutes) → une à la fois | `lister_factures` | ❌ | `paiement-vs-liste`, `chiffre-arabizi` |
| 5 | 5lshome kamline | latin | `payer_facture` (toutes) | FAQ, rien trouvé | ❌ | `faq-mal-routee` |
| 7 | 5lsse facture dyal 312dh | latin | `payer_facture` (montant 312) | `lister_factures` | ❌ | `paiement-vs-liste` (le LLM n'utilise pas `montant`) |
| 9 | 5lsse facture dyal 249dh | latin | `payer_facture` (montant 249) | `lister_factures` | ❌ | `paiement-vs-liste` |
| 11 | 5lse tous les factures | mélange | `payer_facture` (toutes) | `lister_factures` | ❌ | `paiement-vs-liste`, `chiffre-arabizi` |
| 13 | payer tous les factures | français | `payer_facture` (toutes) | « wa7da b wa7da » + liste | ✅ | |
| 15 | 5lsse liya tous les factures | mélange | idem | `lister_factures` | ❌ | `chiffre-arabizi` |
| 17 | 5lsse  tous les factures | mélange | idem | `lister_factures` | ❌ | `chiffre-arabizi` |
| 19 | 5lse liya tous les factures | mélange | idem | `lister_factures` | ❌ | `chiffre-arabizi` |
| 21 | 5lse eau | mélange | `payer_facture` (eau) | `lister_factures` | ❌ | `chiffre-arabizi` |
| 23 | khlsse liya eau | mélange | `payer_facture` (eau) → carte | carte, 312 DH | ✅ | « kh » au lieu de « 5 » |
| 25 | Non | latin | annulation | « Safi, ma tkhelless walou. » | ✅ | |
| 27 | khlesse liya tous les factures | mélange | `payer_facture` (toutes) | « wa7da b wa7da » + liste | ✅ | « kh » au lieu de « 5 » |
| 29 | khless liya k3e li factures | latin | idem | `lister_factures` | ❌ | `chiffre-arabizi` (« k3e » = tout, pas compris) |
| 31 | khless liya ka3e li factures | latin | idem | `lister_factures` | ❌ | `chiffre-arabizi` |
| 33 | 3tini les trois derniers operations fl compte dyali | mélange | `lister_transactions`, 3 opérations | les 5 dernières | ❌ | `nombre-non-supporte` (le bon outil, mais toujours 5) |
| 35 | nn 3tini hir les 3 dernieres | mélange | idem | les 5 dernières | ❌ | `nombre-non-supporte`, `suite` |
| 37 | 3tini releve bancaire dyal le mois 10 et l'année 2026 | mélange | refus : relevé pas disponible | refus générique | ✅ | refus juste, message générique |
| 39 | ajouter liya un bénéfiaires fl compte dyal numero de compte 1234567890112341234543642, smiya kamla : Layla Lolila | mélange | FAQ « Bénéficiaires » (on ne peut pas en ajouter) | refus générique | ❌ | `faq-mal-routee` |
| 41 | hhhhhh | latin | rire : politesse, sans outil | refus | ❌ | `politesse` |

**Piste pour le benchmark** : sur les mêmes demandes, « khlsse liya eau » et « khlesse liya tous les factures » réussissent, alors que « 5lse eau » et « 5lse liya tous les factures » échouent. Une étape qui récrirait les chiffres de l'arabizi avant le LLM (5 → kh, 3 → ع…) serait une variante à mesurer, à côté de la comparaison des modèles.

