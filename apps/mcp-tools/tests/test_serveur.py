"""Tests du serveur MCP, en HTTP, avec le client MCP officiel (comme agent-api)."""

from decimal import Decimal

import pytest


def resultat(appel):
    assert not appel.is_error, appel.content
    return appel.structured_content


# --- Ce que le serveur annonce ------------------------------------------------------------------------------------


def test_le_serveur_annonce_ses_cinq_outils_et_ce_qu_ils_font(mcp):
    outils = {o.name: o for o in mcp.lister()}

    assert sorted(outils) == [
        "consulter_solde",
        "faire_virement",
        "lister_factures",
        "lister_transactions",
        "payer_facture",
    ]
    for lecture in ("consulter_solde", "lister_transactions", "lister_factures"):
        assert outils[lecture].annotations.read_only_hint is True
    for operation in ("payer_facture", "faire_virement"):
        assert (
            outils[operation].annotations.destructive_hint is True
        )  # un client bien fait demande l'accord de l'humain
    fournisseur = outils["payer_facture"].input_schema["properties"]["fournisseur"]
    assert fournisseur["anyOf"][0]["enum"] == ["eau_electricite", "internet", "mobile"]  # liste fermée


# --- Le client vient de l'en-tête, jamais d'un argument -----------------------------------------------------------


def test_le_client_vient_de_l_en_tete(mcp, fausse_banque):
    assert resultat(mcp("consulter_solde", client_id=2))["solde"] == "150.00"
    assert fausse_banque.appels == [("solde", 2)]


def test_sans_en_tete_le_serveur_refuse(mcp, fausse_banque):
    appel = mcp("consulter_solde", client_id=None)

    assert appel.is_error
    assert "X-Client-Id" in appel.content[0].text
    assert fausse_banque.appels == []


def test_les_listes_sont_rangees_sous_un_nom(mcp):
    assert resultat(mcp("lister_transactions"))["transactions"][0]["libelle"] == "Café"
    assert [f["id"] for f in resultat(mcp("lister_factures"))["factures"]] == [1, 2]


# --- Rien ne bouge sans la confirmation du client -----------------------------------------------------------------


def test_sans_confirmation_un_paiement_n_est_qu_une_verification(mcp, fausse_banque):
    apercu = resultat(mcp("payer_facture", {"fournisseur": "eau_electricite"}))

    assert (apercu["simulation"], apercu["nouveau_solde"]) == (True, "2038.00")
    assert fausse_banque.appels == [("paiement", 1, 1, True)]
    assert fausse_banque.soldes[1] == Decimal("2350.00")


def test_avec_la_confirmation_le_paiement_est_fait(mcp, fausse_banque):
    fait = resultat(mcp("payer_facture", {"facture_id": 1}, confirmation="oui"))

    assert fait["simulation"] is False
    assert fausse_banque.soldes[1] == Decimal("2038.00")


@pytest.mark.parametrize("confirmation", ["Oui", "peut-être", "true"])
def test_une_confirmation_qui_n_est_pas_exactement_oui_ne_suffit_pas(mcp, fausse_banque, confirmation):
    assert resultat(mcp("payer_facture", {"facture_id": 1}, confirmation=confirmation))["simulation"] is True
    assert fausse_banque.soldes[1] == Decimal("2350.00")


# --- Paiement : trouver la facture --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("arguments", "code"),
    [
        ({}, "fournisseur_manquant"),
        ({"fournisseur": "mobile"}, "facture_absente"),
        ({"facture_id": 7}, "facture_introuvable"),  # elle existe, mais c'est une facture de Youssef
        ({"facture_id": 99}, "facture_introuvable"),
    ],
)
def test_une_facture_introuvable_donne_un_refus_avec_un_code(mcp, fausse_banque, arguments, code):
    assert resultat(mcp("payer_facture", arguments))["refus"]["code"] == code
    assert fausse_banque.appels == []


def test_le_refus_de_la_banque_est_transmis_avec_ses_chiffres(mcp):
    refus = resultat(mcp("payer_facture", {"fournisseur": "internet"}, client_id=2))["refus"]

    assert refus == {
        "code": "solde_insuffisant",
        "message": "Solde insuffisant",
        "solde": "150.00",
        "montant": "349.00",
    }


# --- Virement : trouver le bénéficiaire et lire le montant --------------------------------------------------------


@pytest.mark.parametrize("nom", ["Fatima", "fatima", "l Fatima", "l'Fatima", "à Fatima Lahlou", "LAHLOU"])
def test_le_beneficiaire_est_trouve_malgre_les_petits_mots(mcp, fausse_banque, nom):
    apercu = resultat(mcp("faire_virement", {"beneficiaire": nom, "montant": 500}))

    assert (apercu["beneficiaire_id"], apercu["beneficiaire"], apercu["montant"]) == (1, "Fatima Lahlou", "500.00")
    assert fausse_banque.appels == [("virement", 1, 1, Decimal("500.00"), True)]


@pytest.mark.parametrize(
    ("arguments", "client_id", "code"),
    [
        ({"montant": 100}, 1, "beneficiaire_manquant"),
        ({"beneficiaire": "Mehdi", "montant": 100}, 1, "beneficiaire_inconnu"),
        ({"beneficiaire": "Fatima", "montant": 100}, 3, "beneficiaire_ambigu"),  # deux Fatima chez Nadia
    ],
)
def test_un_beneficiaire_introuvable_ou_ambigu_donne_un_refus(mcp, fausse_banque, arguments, client_id, code):
    assert resultat(mcp("faire_virement", arguments, client_id=client_id))["refus"]["code"] == code
    assert fausse_banque.appels == []


@pytest.mark.parametrize("montant", [0, -50, "-50", "bezaf", None, "NaN", "12.345"])
def test_un_montant_invalide_n_est_jamais_corrige_en_silence(mcp, fausse_banque, montant):
    assert resultat(mcp("faire_virement", {"beneficiaire": "Fatima", "montant": montant}))["refus"]["code"] == (
        "montant_invalide"
    )
    assert fausse_banque.appels == []


@pytest.mark.parametrize(("montant", "attendu"), [("2 000 DH", "2000.00"), ("1 000,50", "1000.50"), (750, "750.00")])
def test_les_montants_ecrits_a_la_marocaine_sont_lus(mcp, montant, attendu):
    assert resultat(mcp("faire_virement", {"beneficiaire": "Omar", "montant": montant}))["montant"] == attendu


def test_le_plafond_est_verifie_par_la_banque(mcp):
    refus = resultat(mcp("faire_virement", {"beneficiaire": "Fatima Lahlou", "montant": 3000}, client_id=3))["refus"]
    assert (refus["code"], refus["plafond"]) == ("plafond_depasse", "2000.00")


def test_un_virement_confirme_avec_l_identifiant_exact(mcp, fausse_banque):
    fait = resultat(mcp("faire_virement", {"beneficiaire_id": 1, "montant": "500.00"}, confirmation="oui"))

    assert (fait["simulation"], fait["nouveau_solde"]) == (False, "1850.00")
    assert fausse_banque.appels == [("virement", 1, 1, Decimal("500.00"), False)]
