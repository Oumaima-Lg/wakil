"""Le déroulé d'un paiement et d'un virement : retrouver ce que le client désigne, puis le demander à la banque.

Aucun type MCP ici (serveur.py fait le branchement) : équivalent Spring d'un @Service derrière un @RestController.
Les règles (solde, plafond, facture déjà payée) restent dans la banque : ici, on retrouve seulement la facture, le
bénéficiaire et le montant. confirme=False : vérification à blanc, la banque vérifie et calcule tout, puis annule.
"""

from decimal import Decimal
from typing import Any

from app import banque
from app.recherche import FOURNISSEURS, lire_montant, trouver_beneficiaires


def refus(code: str, message: str, **details: Any) -> dict[str, Any]:
    """Une demande que la banque ou le serveur ne peut pas exécuter : une réponse normale, avec un code lisible."""
    return {"refus": {"code": code, "message": message, **details}}


def payer_facture(
    client_id: int,
    fournisseur: str | None,
    facture_id: int | None,
    confirme: bool,
    montant: float | str | None = None,
) -> dict[str, Any]:
    """La facture se désigne par son identifiant (bouton du front), son fournisseur, son montant, ou les deux.
    fournisseur « toutes » : une facture par carte de confirmation ; s'il y en a plusieurs, on demande laquelle."""
    impayees = banque.factures_impayees(client_id)
    if facture_id is not None:  # bouton « Payer avec Wakil » : une facture précise, qui doit être à ce client
        facture = next((f for f in impayees if f["id"] == facture_id), None)
        if facture is None:
            return refus("facture_introuvable", "Facture introuvable parmi les factures à payer")
    else:
        if fournisseur == "toutes" and len(impayees) > 1:
            factures = [{"fournisseur": f["fournisseur"], "montant": f["montant"]} for f in impayees]
            return refus("une_a_la_fois", "Une seule facture par confirmation", factures=factures)
        if fournisseur in FOURNISSEURS:
            # S'il y en a plusieurs du même fournisseur, la plus ancienne d'abord (la banque les rend par id).
            candidates = [f for f in impayees if f["fournisseur"] == FOURNISSEURS[fournisseur]]
        elif fournisseur == "toutes" or montant is not None:
            candidates = impayees
        else:
            return refus("fournisseur_manquant", "Quel fournisseur ?")
        if montant is not None:  # « la facture de 249 DH »
            somme: Decimal | None = lire_montant(montant)
            if somme is None:
                return refus("montant_invalide", "Montant absent ou invalide")
            candidates = [f for f in candidates if Decimal(f["montant"]) == somme]
            if not candidates:
                return refus("facture_absente", "Aucune facture à payer de ce montant", montant=f"{somme:.2f}")
        if not candidates:
            if fournisseur in FOURNISSEURS:
                return refus(
                    "facture_absente",
                    "Aucune facture à payer pour ce fournisseur",
                    fournisseur=FOURNISSEURS[fournisseur],
                )
            return refus("facture_absente", "Aucune facture à payer")
        facture = candidates[0]
    try:
        return banque.payer(client_id, facture["id"], simulation=not confirme)
    except banque.RefusBanque as erreur:  # solde insuffisant, facture déjà payée…
        return {"refus": erreur.detail}


def faire_virement(
    client_id: int, beneficiaire: str | None, montant: float | str | None, beneficiaire_id: int | None, confirme: bool
) -> dict[str, Any]:
    beneficiaires = banque.beneficiaires(client_id)
    if beneficiaire_id is not None:
        candidats = [b for b in beneficiaires if b["id"] == beneficiaire_id]
    else:
        nom = (beneficiaire or "").strip()
        if not nom:
            return refus("beneficiaire_manquant", "À quel bénéficiaire ?")
        candidats = trouver_beneficiaires(beneficiaires, nom)
        if len(candidats) > 1:
            return refus("beneficiaire_ambigu", "Plusieurs bénéficiaires portent ce nom", nom=nom)
    if not candidats:
        return refus("beneficiaire_inconnu", "Bénéficiaire inconnu", nom=(beneficiaire or "").strip())
    somme: Decimal | None = lire_montant(montant)
    if somme is None:
        return refus("montant_invalide", "Montant absent ou invalide")
    try:
        resultat = banque.virer(client_id, candidats[0]["id"], somme, simulation=not confirme)
    except banque.RefusBanque as erreur:  # plafond dépassé, solde insuffisant…
        return {"refus": erreur.detail}
    return {"beneficiaire_id": candidats[0]["id"], **resultat}
