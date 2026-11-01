"""Tests des phrases de Wakil."""

import pytest

from app import reponses


@pytest.mark.parametrize(
    ("montant", "attendu"),
    [("2350.00", "2 350 DH"), ("18500", "18 500 DH"), ("-57.98", "-57,98 DH"), ("0.5", "0,50 DH")],
)
def test_montant_a_la_marocaine(montant, attendu):
    assert reponses.dh(montant) == attendu


def test_factures_impayees():
    factures = [
        {"fournisseur": "Eau & Électricité (démo)", "montant": "312.00"},
        {"fournisseur": "Internet (démo)", "montant": "249.00"},
    ]
    assert reponses.factures(factures).startswith("3ndek 2 factures mazal ma tkhelsou (561 DH f lmjmou3)")


def test_une_seule_facture_impayee_au_singulier():
    factures = [{"fournisseur": "Internet (démo)", "montant": "349.00"}]
    assert reponses.factures(factures) == "3ndek facture wa7da mazal ma tkhelsat :\n- Internet (démo) : 349 DH"


def test_aucune_facture_impayee():
    assert reponses.factures([]) == "Ma 3ndek hta facture mazal ma tkhelsat."


def test_date_affichee_a_l_heure_du_maroc():
    # En juillet 2026, le Maroc était à UTC+1 (base tzdata) : 23 h 30 UTC le 9, c'est déjà le 10 à 0 h 30.
    # Ne jamais écrire « +1 heure » en dur : selon tzdata 2026c, le Maroc est repassé à UTC+0 le 20/09/2026.
    transaction = {"date": "2026-07-09T23:30:00Z", "libelle": "Café", "montant": "-20.00"}
    assert "- 10/07 · Café : -20 DH" in reponses.transactions({"transactions": [transaction]})


# --- Morceau 15 : plafond, « toutes les factures », facture désignée par son montant ----------------------------------


def test_plafond_du_compte():
    assert reponses.plafond({"plafond_virement": "10000.00"}) == "Plafond dyalek howa 10 000 DH l kol virement."


def test_une_facture_a_la_fois_liste_les_factures_et_demande_laquelle():
    detail = {"code": "une_a_la_fois", "factures": [{"fournisseur": "Eau & Électricité (démo)", "montant": "312.00"},
                                                    {"fournisseur": "Internet (démo)", "montant": "249.00"}]}  # fmt: skip

    assert reponses.refus("paiement", detail) == (
        "N9der nkhelless ghir facture wa7da f kol merra. 3ndek :\n"
        "- Eau & Électricité (démo) : 312 DH\n- Internet (démo) : 249 DH\nChmen wa7da nbda ?"
    )


@pytest.mark.parametrize(
    ("detail", "attendu"),
    [
        ({"montant": "999.00"}, "Ma 3ndek hta facture dyal 999 DH mazal ma tkhelsat."),
        ({"fournisseur": "Mobile (démo)"}, "Ma 3ndek hta facture dyal Mobile (démo) mazal ma tkhelsat."),
        ({}, "Ma 3ndek hta facture mazal ma tkhelsat."),
    ],
)
def test_aucune_facture_selon_ce_que_le_client_a_designe(detail, attendu):
    assert reponses.refus("paiement", {"code": "facture_absente", **detail}) == attendu


# --- Bénéficiaires et dépenses : les nombres et les totaux viennent du serveur MCP et de la banque --------------------


def test_beneficiaires_avec_leur_nombre():
    resultat = {
        "beneficiaires": [
            {"nom": "Fatima Lahlou", "rib_masque": "•••• 8633"},
            {"nom": "Omar Benali", "rib_masque": "•••• 1120"},
        ],
        "nombre": 2,
    }
    assert reponses.beneficiaires(resultat) == (
        "3ndek 2 bénéficiaires :\n- Fatima Lahlou (•••• 8633)\n- Omar Benali (•••• 1120)"
    )


def test_aucun_beneficiaire():
    assert reponses.beneficiaires({"beneficiaires": [], "nombre": 0}) == "Ma 3ndek hta bénéficiaire."


DEPENSES_OCTOBRE = {
    "periode": "ce_mois",
    "du": "2026-10-01",
    "au": "2026-10-30",
    "depenses": "1012.50",
    "entrees": "6000.00",
    "nombre": 5,
    "par_categorie": [
        {"categorie": "virements", "nom": "Virements envoyés", "total": "500.00", "nombre": 1},
        {"categorie": "factures", "nom": "Factures", "total": "312.00", "nombre": 1},
        {"categorie": "restaurant", "nom": "Restaurant", "total": "200.50", "nombre": 2},
    ],
    "plus_grosse": {"id": 9, "date": "2026-10-20T10:00:00Z", "montant": "-500.00", "libelle": "Virement vers Fatima"},
    "categorie": None,
}


def test_depenses_du_mois():
    assert reponses.depenses(DEPENSES_OCTOBRE) == (
        "Had chhar (octobre) : srefti 1 012,50 DH w dkhel lik 6 000 DH (5 d l'opérations).\n"
        "Fin srefti ktar :\n- Virements envoyés : 500 DH\n- Factures : 312 DH\n- Restaurant : 200,50 DH\n"
        "Akbar masrouf : Virement vers Fatima, 500 DH (20/10)."
    )


def test_depenses_d_une_categorie_le_mois_dernier():
    resultat = DEPENSES_OCTOBRE | {
        "periode": "mois_dernier",
        "du": "2026-09-01",
        "categorie": {"categorie": "restaurant", "nom": "Restaurant", "total": "200.50", "nombre": 2},
    }
    assert reponses.depenses(resultat) == (
        "Chhar li fat (septembre), srefti 200,50 DH f Restaurant (2 d l'opérations)."
    )


def test_depenses_d_une_categorie_vide():
    resultat = DEPENSES_OCTOBRE | {"categorie": {"categorie": "taxi", "nom": "Taxi", "total": "0.00", "nombre": 0}}
    assert reponses.depenses(resultat) == "Ma srefti walou f Taxi had chhar (octobre)."


# --- Relevé, cartes et blocage --------------------------------------------------------------------------------------

RELEVE = {
    "transactions": [{"date": "2026-09-12T10:00:00Z", "libelle": "Salaire (démo)", "montant": "6000.00"}],
    "releve": {"mois": "2026-09", "du": "2026-09-01", "au": "2026-09-30", "complet": True, "solde_ouverture": "1000.00",
               "total_entrees": "6000.00", "total_sorties": "0.00", "solde_cloture": "7000.00"},
}  # fmt: skip


def test_releve_d_un_mois_avec_ses_soldes():
    assert reponses.transactions(RELEVE) == (
        "Relevé dyal septembre 2026 : bdit b 1 000 DH, dkhel 6 000 DH, khrej 0 DH, w salit b 7 000 DH.\n"
        "- 12/09 · Salaire (démo) : 6 000 DH"
    )


def test_releve_du_mois_en_cours_et_mois_vide():
    en_cours = RELEVE | {"releve": RELEVE["releve"] | {"complet": False}}
    assert reponses.transactions(en_cours).startswith("Relevé dyal septembre 2026 (chhar mazal ma salach) :")
    assert reponses.transactions(RELEVE | {"transactions": []}) == "Ma kayna hta opération f septembre 2026."


def test_l_etat_des_cartes():
    carte = {"numero_masque": "•••• 7919", "expiration": "02/29", "statut": "bloquee", "motif_opposition": None}
    assert reponses.cartes([carte]) == "3ndek carte wa7da :\n- •••• 7919 : mbloquia (kat-sala f 02/29)"
    assert reponses.cartes([]) == "Ma 3ndek hta carte."


def test_la_carte_de_confirmation_d_un_blocage_dit_comment_debloquer():
    texte = reponses.confirmation({"type": "blocage", "numero_masque": "•••• 7919"})

    assert texte == (
        "Hahiya l'carte li bghiti nbloqui : •••• 7919. Tqder tdebloquiha men b3d f l'espace dyalek (Ma carte).\n"
        "Wach nbloqui l'carte ? (Oui / La)"
    )
    assert reponses.operation_faite("blocage", {"numero_masque": "•••• 7919"}).startswith("Tbloquat l'carte •••• 7919.")


@pytest.mark.parametrize(
    ("detail", "debut"),
    [
        ({"code": "carte_deja_bloquee"}, "L'carte deja mbloquia."),
        ({"code": "carte_en_opposition"}, "Had l'carte f opposition"),
        (
            {"code": "carte_ambigue", "cartes": ["•••• 3757", "•••• 1200"]},
            "3ndek ktar men carte (•••• 3757, •••• 1200).",
        ),
        ({"code": "carte_introuvable"}, "Ma l9itch had l'carte"),
        ({"code": "autre"}, "Smeh lia, l'banque rfdat l'blocage."),
    ],
)
def test_les_refus_d_un_blocage(detail, debut):
    assert reponses.refus("blocage", detail).startswith(debut)
