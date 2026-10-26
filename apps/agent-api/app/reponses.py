"""Les phrases de Wakil. Les montants viennent de la banque et sont écrits par ce code, jamais par le LLM."""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

MAROC = ZoneInfo("Africa/Casablanca")

SALUT = "Wa 3alikom salam ! Ana Wakil, l'assistant dyal Banque Atlas Démo. Kifach n9der n3awnek ?"
POLITESSE = "Bla jmil ! Ila bghiti chi haja okhra, ana hna."
# Neutre : convient au hors-sujet, à ce qui n'est pas encore possible (virement, paiement) et à l'incompris.
REFUS = (
    "Smeh lia, ma fhemtch wla ma n9derch ndir had l7aja. N9der n3awnek f : solde, l'opérations w les factures dyalek."
)
ERREUR = "Smeh lia, kayn mochkil f la banque daba. 3awed men ba3d."
PANNE = "Smeh lia, Wakil ma khdamch daba. 3awed men ba3d."  # panne de l'agent lui-même (LLM injoignable…)


def dh(montant: str | Decimal) -> str:
    """Montant à la marocaine : « 2 350 DH », « -57,98 DH »."""
    texte = f"{Decimal(montant):,.2f}".replace(",", " ").replace(".", ",")
    return f"{texte.removesuffix(',00')} DH"


def solde(resultat: dict) -> str:
    return f"Solde dyalek howa {dh(resultat['solde'])}."


def transactions(resultat: list[dict]) -> str:
    lignes = [
        f"- {datetime.fromisoformat(t['date']).astimezone(MAROC):%d/%m} · {t['libelle']} : {dh(t['montant'])}"
        for t in resultat
    ]
    return "Hahoma akhir l'opérations dyalek :\n" + "\n".join(lignes)


def factures(resultat: list[dict]) -> str:
    if not resultat:
        return "Ma 3ndek hta facture mazal ma tkhelsat."
    lignes = [f"- {f['fournisseur']} : {dh(f['montant'])}" for f in resultat]
    if len(resultat) == 1:
        return "3ndek facture wa7da mazal ma tkhelsat :\n" + lignes[0]
    total = sum(Decimal(f["montant"]) for f in resultat)
    return f"3ndek {len(resultat)} factures mazal ma tkhelsou ({dh(total)} f lmjmou3) :\n" + "\n".join(lignes)


# Opérations (paiement, virement). Wakil parle de ce qu'il fait lui-même (nkhelless, nsifet) : la phrase est la même
# pour une cliente et pour un client.
QUEL_FOURNISSEUR = "Ach men facture bghiti nkhelless : l'eau w l'électricité, internet wla mobile ?"
QUEL_BENEFICIAIRE = "L chkoun bghiti nsifet ? 3tini smiyto kif ma kayna f les bénéficiaires dyalek."
QUEL_MONTANT = "Chhal bghiti nsifet ?"
CONFIRMATION_INCOMPRISE = "Ma fhemtch jawab dyalek, donc ma dert walou. Ila bghiti, 3awed talab."
# Après un « oui », si la banque ne répond pas, on ne sait pas si l'opération est passée : on le dit honnêtement.
ERREUR_OPERATION = "Smeh lia, kayn mochkil f la banque. Chouf l'opérations dyalek 9bel ma t3awed."
ANNULEE = {"paiement": "Safi, ma tkhelless walou.", "virement": "Safi, ma tsifet walou."}


def pas_de_facture(fournisseur: str) -> str:
    return f"Ma 3ndek hta facture dyal {fournisseur} mazal ma tkhelsat."


def beneficiaire_inconnu(nom: str) -> str:
    return f"Ma l9itch « {nom} » f les bénéficiaires dyalek."


def beneficiaire_ambigu(nom: str) -> str:
    return f"3ndek ktar men bénéficiaire smito « {nom} ». 3tini smiya kamla."


def confirmation(operation: dict) -> str:
    """Le texte de la carte « Wach nconfirmi ? », avec les montants de la vérification à blanc."""
    apres = f"Solde dyalek men b3d : {dh(operation['nouveau_solde'])}."
    if operation["type"] == "paiement":
        return (
            f"Hahiya l'facture li bghiti nkhelless : {operation['fournisseur']}, {dh(operation['montant'])}. {apres}\n"
            "Wach nconfirmi l'paiement ? (Oui / La)"
        )
    return (
        f"Hahowa l'virement li bghiti ndir : {dh(operation['montant'])} l {operation['beneficiaire']} "
        f"({operation['beneficiaire_rib_masque']}). {apres}\nWach nconfirmi l'virement ? (Oui / La)"
    )


def operation_faite(type_operation: str, resultat: dict) -> str:
    fait = "Tkhelssat" if type_operation == "paiement" else "Tsifet"
    return f"{fait} ! Solde jdid dyalek : {dh(resultat['nouveau_solde'])}."


def refus(type_operation: str, detail: dict) -> str:
    """Le refus de la banque, expliqué avec ses propres chiffres (code et montants : voir bank-api)."""
    quoi = "l'paiement" if type_operation == "paiement" else "l'virement"
    code = detail.get("code")
    if code == "solde_insuffisant":
        besoin = (
            f"l had l'facture ({dh(detail['montant'])})"
            if type_operation == "paiement"
            else f"bach nsifet {dh(detail['montant'])}"
        )
        return f"Smeh lia, l'banque rfdat {quoi} : solde dyalek ({dh(detail['solde'])}) ma kafich {besoin}."
    if code == "plafond_depasse":
        return (
            f"Smeh lia, l'banque rfdat l'virement : {dh(detail['montant'])} "
            f"kaydouz l'plafond dyalek ({dh(detail['plafond'])})."
        )
    if code == "facture_deja_payee":
        return "Had l'facture deja tkhelsat."
    if code == "virement_vers_soi":
        return "Ma n9derch ndir virement l compte dyalek."
    return f"Smeh lia, l'banque rfdat {quoi}."
