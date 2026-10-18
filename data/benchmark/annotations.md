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
