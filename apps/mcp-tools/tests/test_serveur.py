"""Tests du serveur MCP, en HTTP, avec le client MCP officiel (comme agent-api)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import analyse


def resultat(appel):
    assert not appel.is_error, appel.content
    return appel.structured_content


# --- Ce que le serveur annonce ------------------------------------------------------------------------------------


LECTURES = ["analyser_depenses", "consulter_cartes", "consulter_plafond", "consulter_solde", "lister_beneficiaires",
            "lister_factures", "lister_transactions"]  # fmt: skip
OPERATIONS = ["bloquer_carte", "faire_virement", "payer_facture"]


def test_le_serveur_annonce_ses_dix_outils_et_ce_qu_ils_font(mcp):
    outils = {o.name: o for o in mcp.lister()}

    assert sorted(outils) == sorted([*LECTURES, *OPERATIONS])
    for lecture in LECTURES:
        assert outils[lecture].annotations.read_only_hint is True
    for operation in OPERATIONS:
        assert (
            outils[operation].annotations.destructive_hint is True
        )  # un client bien fait demande l'accord de l'humain
    fournisseur = outils["payer_facture"].input_schema["properties"]["fournisseur"]
    assert fournisseur["anyOf"][0]["enum"] == ["eau_electricite", "internet", "mobile", "toutes"]  # liste fermée


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


def test_les_beneficiaires_et_leur_nombre_sans_identifiant(mcp):
    assert resultat(mcp("lister_beneficiaires")) == {
        "beneficiaires": [{"nom": "Fatima Lahlou", "rib_masque": "•••• 8633"},
                          {"nom": "Omar Benali", "rib_masque": "•••• 1120"}],
        "nombre": 2,
    }  # fmt: skip
    assert resultat(mcp("lister_beneficiaires", client_id=2)) == {"beneficiaires": [], "nombre": 0}


def test_les_depenses_sont_calculees_par_la_banque(mcp, fausse_banque):
    depenses = resultat(mcp("analyser_depenses", {"periode": "mois_dernier"}))

    ((_, client, du, au),) = fausse_banque.appels
    # tout un mois : du 1er au dernier jour
    assert (
        client == 1 and du.day == 1 and (au.year, au.month) == (du.year, du.month) and (au + timedelta(days=1)).day == 1
    )
    assert depenses["periode"] == "mois_dernier" and depenses["depenses"] == "512.50" and depenses["categorie"] is None


@pytest.mark.parametrize(
    ("categorie", "ligne"),
    [("restaurant", {"categorie": "restaurant", "nom": "Restaurant", "total": "200.50", "nombre": 2}),
     ("taxi", {"categorie": "taxi", "nom": "Taxi", "total": "0.00", "nombre": 0})],
)  # fmt: skip
def test_les_depenses_d_une_categorie_meme_vide(mcp, categorie, ligne):
    assert resultat(mcp("analyser_depenses", {"categorie": categorie}))["categorie"] == ligne


def test_une_categorie_hors_de_la_liste_est_refusee(mcp, fausse_banque):
    assert mcp("analyser_depenses", {"categorie": "voyages"}).is_error
    assert fausse_banque.appels == []


@pytest.mark.parametrize(
    ("periode", "aujourd_hui", "attendu"),
    [("ce_mois", date(2026, 10, 30), (date(2026, 10, 1), date(2026, 10, 30))),
     ("mois_dernier", date(2026, 10, 30), (date(2026, 9, 1), date(2026, 9, 30))),
     ("mois_dernier", date(2026, 3, 1), (date(2026, 2, 1), date(2026, 2, 28))),
     ("mois_dernier", date(2026, 1, 15), (date(2025, 12, 1), date(2025, 12, 31)))],
)  # fmt: skip
def test_les_dates_d_un_mois(periode, aujourd_hui, attendu):
    assert analyse.dates(periode, aujourd_hui) == attendu


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


# --- Plafond, « toutes les factures » et facture désignée par son montant (morceau 15) ------------------------------


def test_le_plafond_du_compte_du_client(mcp):
    assert resultat(mcp("consulter_plafond", client_id=3)) == {"plafond_virement": "2000.00"}


def test_toutes_les_factures_une_a_la_fois(mcp, fausse_banque):
    """Une carte de confirmation par facture : s'il y en a plusieurs, on demande laquelle, sans rien vérifier."""
    refus = resultat(mcp("payer_facture", {"fournisseur": "toutes"}))["refus"]

    assert refus["code"] == "une_a_la_fois"
    assert refus["factures"] == [{"fournisseur": "Eau & Électricité (démo)", "montant": "312.00"},
                                 {"fournisseur": "Internet (démo)", "montant": "249.00"}]  # fmt: skip
    assert fausse_banque.appels == []


def test_toutes_avec_une_seule_facture_on_prepare_celle_ci(mcp, fausse_banque):
    resultat(mcp("payer_facture", {"fournisseur": "toutes"}, client_id=2))

    assert fausse_banque.appels == [("paiement", 2, 7, True)]  # la seule facture de Youssef, vérifiée à blanc


@pytest.mark.parametrize("montant", [249, "249 DH", "249,00"])
def test_une_facture_designee_par_son_montant(mcp, montant):
    apercu = resultat(mcp("payer_facture", {"montant": montant}))

    assert (apercu["facture_id"], apercu["fournisseur"], apercu["simulation"]) == (2, "Internet (démo)", True)


@pytest.mark.parametrize(
    ("arguments", "code"),
    [
        ({"montant": 999}, "facture_absente"),
        ({"fournisseur": "eau_electricite", "montant": 249}, "facture_absente"),  # l'eau coûte 312 DH, pas 249
        ({"montant": "bezaf"}, "montant_invalide"),
    ],
)
def test_un_montant_sans_facture_correspondante_donne_un_refus(mcp, fausse_banque, arguments, code):
    assert resultat(mcp("payer_facture", arguments))["refus"]["code"] == code
    assert fausse_banque.appels == []


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


# --- Idempotence : la clé de l'application va jusqu'à la banque ------------------------------------------------------


def test_la_cle_d_idempotence_suit_l_operation_confirmee(mcp, fausse_banque):
    mcp("payer_facture", {"fournisseur": "internet"}, confirmation="oui", idempotence="carte-42")

    assert fausse_banque.cles == ["carte-42"]


def test_sans_cle_l_operation_part_sans_cle(mcp, fausse_banque):
    mcp("faire_virement", {"beneficiaire": "Omar", "montant": 100}, confirmation="oui")

    assert fausse_banque.cles == [None]


@pytest.mark.parametrize(("simulation", "attendu"), [(False, "carte-7"), (True, None)])
def test_l_en_tete_idempotency_key_seulement_pour_une_vraie_operation(monkeypatch, simulation, attendu):
    """Une vérification à blanc ne change rien à la banque : elle ne porte pas de clé."""
    from app import banque as vraie_banque

    envoye = {}

    class Reponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {}

    def post(url, params=None, json=None, headers=None, timeout=None):
        envoye.update(headers)
        return Reponse()

    monkeypatch.setattr(vraie_banque.httpx, "post", post)
    vraie_banque._post(1, "/virements", simulation, json={}, cle="carte-7")

    assert envoye.get("Idempotency-Key") == attendu


# --- Relevé d'un mois et cartes ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("numero", "attendu"), [(10, "2026-10"), (9, "2026-09"), (1, "2026-01"), (11, "2025-11"), (12, "2025-12")]
)
def test_le_mois_du_releve_est_le_dernier_deja_commence(numero, attendu):
    assert analyse.mois_du_releve(numero, date(2026, 10, 31)) == attendu


def test_un_mois_donne_le_releve_avec_son_resume(mcp, fausse_banque):
    lu = resultat(mcp("lister_transactions", {"mois": 9}))

    assert fausse_banque.appels[0][0] == "releve" and fausse_banque.appels[0][2].endswith("-09")
    assert lu["releve"]["solde_cloture"] == "1300.00" and "transactions" not in lu["releve"]
    assert lu["transactions"][0]["libelle"] == "Virement reçu"


def test_sans_mois_les_dernieres_operations(mcp, fausse_banque):
    assert "releve" not in resultat(mcp("lister_transactions"))
    assert fausse_banque.appels == []


def test_un_mois_hors_de_1_a_12_est_refuse(mcp, fausse_banque):
    assert mcp("lister_transactions", {"mois": 13}).is_error
    assert fausse_banque.appels == []


def test_les_cartes_et_leur_etat(mcp):
    assert resultat(mcp("consulter_cartes"))["cartes"] == [
        {"numero_masque": "•••• 7919", "expiration": "02/29", "statut": "active", "motif_opposition": None}
    ]


def test_sans_confirmation_le_blocage_est_seulement_verifie(mcp, fausse_banque):
    carte = resultat(mcp("bloquer_carte"))

    assert (carte["carte_id"], carte["statut"], carte["numero_masque"]) == (1, "bloquee", "•••• 7919")
    assert fausse_banque.appels == [("blocage", 1, 1, True)]


def test_avec_la_confirmation_la_carte_est_bloquee(mcp, fausse_banque):
    mcp("bloquer_carte", {"carte_id": 1}, confirmation="oui")

    assert fausse_banque.appels == [("blocage", 1, 1, False)]


def test_deux_cartes_actives_il_faut_dire_laquelle(mcp, fausse_banque):
    refus = resultat(mcp("bloquer_carte", client_id=3))["refus"]

    assert (refus["code"], refus["cartes"]) == ("carte_ambigue", ["•••• 3757", "•••• 1200"])
    assert fausse_banque.appels == []


@pytest.mark.parametrize("chiffres", ["1200", "la carte qui finit par 1200", "•••• 1200"])
def test_la_carte_designee_par_ses_4_derniers_chiffres(mcp, fausse_banque, chiffres):
    assert resultat(mcp("bloquer_carte", {"carte": chiffres}, client_id=3))["carte_id"] == 4


def test_des_chiffres_qui_ne_correspondent_a_aucune_carte(mcp):
    assert resultat(mcp("bloquer_carte", {"carte": "0000"}))["refus"]["code"] == "carte_introuvable"
