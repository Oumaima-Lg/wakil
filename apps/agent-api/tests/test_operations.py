"""Paiements et virements : la confirmation est obligatoire, et seul un « oui » explicite fait bouger l'argent.

La fausse banque note chaque appel (vérification à blanc ou vrai) : on sait exactement quand l'argent aurait bougé.
"""

import uuid
from decimal import Decimal

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app import agent, banque, reponses
from tests.sse import evenements

EAU, INTERNET = "Eau & Électricité (démo)", "Internet (démo)"
FACTURES = {
    1: [{"id": 1, "fournisseur": EAU, "montant": "312.00"}, {"id": 2, "fournisseur": INTERNET, "montant": "249.00"}],
    2: [{"id": 7, "fournisseur": INTERNET, "montant": "349.00"}],
}
BENEFICIAIRES = {
    1: [{"id": 1, "nom": "Fatima Lahlou", "rib_masque": "•••• 8633"}, {"id": 2, "nom": "Omar Benali", "rib_masque": "•••• 1120"}],
    3: [{"id": 5, "nom": "Fatima Lahlou", "rib_masque": "•••• 8633"}, {"id": 6, "nom": "Fatima Zahra Idrissi", "rib_masque": "•••• 4410"}],
}  # fmt: skip
PLAFONDS = {1: Decimal("10000.00"), 2: Decimal("5000.00"), 3: Decimal("2000.00")}


class FausseBanque:
    """Doublure de bank-api pour les opérations, avec les vraies règles (solde, plafond) et les vrais refus 409."""

    def __init__(self):
        self.soldes = {1: Decimal("2350.00"), 2: Decimal("150.00"), 3: Decimal("18500.00")}
        self.appels = []  # (opération, client, facture ou bénéficiaire, montant, simulation)

    @property
    def vrais_appels(self):
        return [appel for appel in self.appels if not appel[-1]]

    def _refuser_si_solde_insuffisant(self, client_id, montant):
        if montant > self.soldes[client_id]:
            raise banque.RefusBanque(
                {"code": "solde_insuffisant", "message": "Solde insuffisant",
                 "solde": f"{self.soldes[client_id]:.2f}", "montant": f"{montant:.2f}"}
            )  # fmt: skip

    def payer(self, client_id, facture_id, simulation=False):
        facture = next(f for f in FACTURES[client_id] if f["id"] == facture_id)
        montant = Decimal(facture["montant"])
        self.appels.append(("paiement", client_id, facture_id, montant, simulation))
        self._refuser_si_solde_insuffisant(client_id, montant)
        nouveau_solde = self.soldes[client_id] - montant
        if not simulation:
            self.soldes[client_id] = nouveau_solde
        return {**facture, "facture_id": facture_id, "nouveau_solde": f"{nouveau_solde:.2f}", "simulation": simulation}

    def virer(self, client_id, beneficiaire_id, montant, simulation=False):
        beneficiaire = next(b for b in BENEFICIAIRES[client_id] if b["id"] == beneficiaire_id)
        self.appels.append(("virement", client_id, beneficiaire_id, montant, simulation))
        if montant > PLAFONDS[client_id]:
            raise banque.RefusBanque(
                {"code": "plafond_depasse", "message": "Plafond de virement dépassé",
                 "plafond": f"{PLAFONDS[client_id]:.2f}", "montant": f"{montant:.2f}"}
            )  # fmt: skip
        self._refuser_si_solde_insuffisant(client_id, montant)
        nouveau_solde = self.soldes[client_id] - montant
        if not simulation:
            self.soldes[client_id] = nouveau_solde
        return {
            "beneficiaire": beneficiaire["nom"],
            "beneficiaire_rib_masque": beneficiaire["rib_masque"],
            "montant": f"{montant:.2f}",
            "nouveau_solde": f"{nouveau_solde:.2f}",
            "simulation": simulation,
        }


@pytest.fixture
def fausse_banque_operations(monkeypatch):
    fausse = FausseBanque()
    monkeypatch.setattr(banque, "factures_impayees", lambda client_id: FACTURES.get(client_id, []))
    monkeypatch.setattr(banque, "beneficiaires", lambda client_id: BENEFICIAIRES.get(client_id, []))
    monkeypatch.setattr(banque, "payer", fausse.payer)
    monkeypatch.setattr(banque, "virer", fausse.virer)
    return fausse


@pytest.fixture
def ecrire():
    """Envoie un message dans une conversation (une neuve par test) et rend les événements SSE reçus."""
    conversation = str(uuid.uuid4())

    def envoyer(http, texte, conversation_id=conversation):
        return evenements(http.post("/chat", json={"conversation_id": conversation_id, "texte": texte}))

    return envoyer


def reponse(evenements_recus):
    return next(donnees for nom, donnees in evenements_recus if nom == "reponse")["texte"]


# --- Paiement d'une facture -------------------------------------------------------------------------------------


def test_un_paiement_s_arrete_sur_la_carte_de_confirmation(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("payer_facture", {"fournisseur": "eau_electricite"})

    recus = ecrire(salma, "khelless liya la facture dyal l'eau")

    assert [nom for nom, _ in recus] == ["etape", "etape", "confirmation", "fin"]
    carte = recus[2][1]
    assert (carte["type"], carte["fournisseur"], carte["montant"], carte["nouveau_solde"]) == (
        "paiement", EAU, "312.00", "2038.00"
    )  # fmt: skip
    assert carte["texte"].endswith("Wach nconfirmi l'paiement ? (Oui / La)")
    # Seule la vérification à blanc a eu lieu : rien n'est payé tant que Salma n'a pas répondu
    assert fausse_banque_operations.appels == [("paiement", 1, 1, Decimal("312.00"), True)]
    assert fausse_banque_operations.vrais_appels == []


@pytest.mark.parametrize("oui", ["Oui", "oui !", "wakha", "Oui, confirmer", "واخا"])
def test_oui_paye_pour_de_vrai(salma, faux_llm, fausse_banque_operations, ecrire, oui):
    faux = faux_llm("payer_facture", {"fournisseur": "eau_electricite"})
    ecrire(salma, "khelless liya la facture dyal l'eau")

    recus = ecrire(salma, oui)

    assert recus[-2] == (
        "reponse",
        {
            "texte": "Tkhelssat ! Solde jdid dyalek : 2 038 DH.",
            "outil": "payer_facture",
            "donnees": {"id": 1, "fournisseur": EAU, "montant": "312.00", "facture_id": 1,
                        "nouveau_solde": "2038.00", "simulation": False},
            "erreur": False,
        },
    )  # fmt: skip
    assert fausse_banque_operations.vrais_appels == [("paiement", 1, 1, Decimal("312.00"), False)]
    assert faux.appels == 1  # le LLM a compris la demande ; le « oui » est lu par le code, pas par le LLM


@pytest.mark.parametrize(
    ("reponse_client", "attendu"),
    [
        ("La", reponses.ANNULEE["paiement"]),
        ("non", reponses.ANNULEE["paiement"]),
        ("chhal bqa f compte dyali ?", reponses.CONFIRMATION_INCOMPRISE),  # ni oui ni non : on ne touche à rien
        ("ewa", reponses.CONFIRMATION_INCOMPRISE),
    ],
)
def test_sans_oui_explicite_rien_n_est_paye(salma, faux_llm, fausse_banque_operations, ecrire, reponse_client, attendu):
    faux_llm("payer_facture", {"fournisseur": "eau_electricite"})
    ecrire(salma, "khelless liya la facture dyal l'eau")

    assert reponse(ecrire(salma, reponse_client)) == attendu
    assert fausse_banque_operations.vrais_appels == []


def test_un_refus_de_la_banque_est_annonce_sans_demander_de_confirmation(
    connecter, faux_llm, fausse_banque_operations, ecrire
):
    youssef = connecter(2)  # 150 DH pour une facture internet de 349 DH
    faux_llm("payer_facture", {"fournisseur": "internet"})

    recus = ecrire(youssef, "bghit nkhelless internet")

    assert "confirmation" not in [nom for nom, _ in recus]
    assert (
        reponse(recus)
        == "Smeh lia, l'banque rfdat l'paiement : solde dyalek (150 DH) ma kafich l had l'facture (349 DH)."
    )
    assert fausse_banque_operations.vrais_appels == []


def test_pas_de_facture_de_ce_fournisseur(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("payer_facture", {"fournisseur": "mobile"})
    assert reponse(ecrire(salma, "khelless l'mobile")) == reponses.pas_de_facture("Mobile (démo)")


def test_fournisseur_absent_ou_invente_on_demande_lequel(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("payer_facture", {"fournisseur": "gaz"})  # pas dans la liste fermée
    assert reponse(ecrire(salma, "khelless l'facture")) == reponses.QUEL_FOURNISSEUR


def test_la_banque_revérifie_au_moment_du_oui(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("payer_facture", {"fournisseur": "eau_electricite"})
    ecrire(salma, "khelless liya la facture dyal l'eau")
    fausse_banque_operations.soldes[1] = Decimal("100.00")  # le solde a baissé entre la carte et le « oui »

    assert reponse(ecrire(salma, "Oui")).startswith("Smeh lia, l'banque rfdat l'paiement : solde dyalek (100 DH)")
    assert fausse_banque_operations.soldes[1] == Decimal("100.00")


# --- Virement ---------------------------------------------------------------------------------------------------


def test_un_virement_trouve_le_beneficiaire_par_son_prenom(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("faire_virement", {"beneficiaire": "fatima", "montant": 500})

    carte = dict(ecrire(salma, "sifet 500 DH l fatima"))["confirmation"]

    assert (carte["beneficiaire"], carte["beneficiaire_rib_masque"], carte["montant"], carte["nouveau_solde"]) == (
        "Fatima Lahlou", "•••• 8633", "500.00", "1850.00"
    )  # fmt: skip
    assert reponse(ecrire(salma, "oui")) == "Tsifet ! Solde jdid dyalek : 1 850 DH."
    assert fausse_banque_operations.vrais_appels == [("virement", 1, 1, Decimal("500.00"), False)]


@pytest.mark.parametrize("nom", ["l Fatima", "l'Fatima", "à Fatima Lahlou", "LAHLOU"])
def test_le_beneficiaire_est_trouve_malgre_les_petits_mots(salma, faux_llm, fausse_banque_operations, ecrire, nom):
    faux_llm("faire_virement", {"beneficiaire": nom, "montant": 100})
    assert dict(ecrire(salma, f"sifet 100 DH {nom}"))["confirmation"]["beneficiaire"] == "Fatima Lahlou"


def test_beneficiaire_inconnu(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("faire_virement", {"beneficiaire": "Mehdi", "montant": 200})
    assert reponse(ecrire(salma, "sifet 200 l Mehdi")) == reponses.beneficiaire_inconnu("Mehdi")


def test_deux_beneficiaires_du_meme_prenom_on_demande_le_nom_complet(
    connecter, faux_llm, fausse_banque_operations, ecrire
):
    faux_llm("faire_virement", {"beneficiaire": "Fatima", "montant": 200})
    assert reponse(ecrire(connecter(3), "sifet 200 l Fatima")) == reponses.beneficiaire_ambigu("Fatima")


@pytest.mark.parametrize("montant", [0, -50, "-50", "bezaf", None, "NaN", "12.345"])
def test_montant_absent_ou_invalide_on_demande_combien(salma, faux_llm, fausse_banque_operations, ecrire, montant):
    faux_llm("faire_virement", {"beneficiaire": "Fatima", "montant": montant})
    assert reponse(ecrire(salma, "sifet l Fatima")) == reponses.QUEL_MONTANT
    assert fausse_banque_operations.appels == []


def test_virement_au_dessus_du_plafond_refuse_d_avance(connecter, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("faire_virement", {"beneficiaire": "Fatima Lahlou", "montant": "3 000 DH"})

    recus = ecrire(connecter(3), "sifet 3000 DH l Fatima Lahlou")

    assert reponse(recus) == "Smeh lia, l'banque rfdat l'virement : 3 000 DH kaydouz l'plafond dyalek (2 000 DH)."
    assert fausse_banque_operations.vrais_appels == []


# --- Sécurité et durabilité -------------------------------------------------------------------------------------


def test_un_autre_client_ne_peut_pas_confirmer_a_ma_place(salma, connecter, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("payer_facture", {"fournisseur": "eau_electricite"})
    conversation = str(uuid.uuid4())
    ecrire(salma, "khelless liya la facture dyal l'eau", conversation)

    # Youssef envoie « Oui » avec le même identifiant de conversation : chez lui, rien n'attend de confirmation
    ecrire(connecter(2), "Oui", conversation)

    assert fausse_banque_operations.vrais_appels == []
    assert reponse(ecrire(salma, "Oui", conversation)).startswith("Tkhelssat")  # la carte de Salma attendait toujours


def test_la_confirmation_survit_a_un_redemarrage(faux_llm, fausse_banque_operations):
    """L'état en attente est dans le checkpointer, pas dans l'objet graphe : un « nouveau processus » le retrouve."""
    faux_llm("payer_facture", {"fournisseur": "eau_electricite"})
    memoire = InMemorySaver()  # en production : PostgresSaver, qui survit vraiment à un redémarrage
    conf = agent.config(1, str(uuid.uuid4()))
    avant = agent.construire(memoire)
    avant.invoke(agent.nouveau_tour("khelless liya l'eau", 1), conf)

    apres = agent.construire(memoire)  # comme après un redémarrage d'agent-api
    etat = apres.invoke(agent.prochaine_entree(apres, "Oui", 1, conf), conf)

    assert etat["reponse"] == "Tkhelssat ! Solde jdid dyalek : 2 038 DH."
    assert fausse_banque_operations.vrais_appels == [("paiement", 1, 1, Decimal("312.00"), False)]
