"""Paiements et virements : la confirmation est obligatoire, et seul un « oui » explicite fait bouger l'argent.

Le faux serveur MCP suit le contrat du vrai (apps/mcp-tools) : sans confirmation dans l'appel, il ne fait qu'une
vérification à blanc. Il note chaque appel : on sait exactement quand l'argent aurait bougé, et avec quoi.
"""

import uuid
from decimal import Decimal, InvalidOperation

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app import agent, outils, reponses
from tests.sse import evenements

EAU, INTERNET = "Eau & Électricité (démo)", "Internet (démo)"
FOURNISSEURS = {"eau_electricite": EAU, "internet": INTERNET, "mobile": "Mobile (démo)"}
FACTURES = {
    1: [{"id": 1, "fournisseur": EAU, "montant": "312.00"}, {"id": 2, "fournisseur": INTERNET, "montant": "249.00"}],
    2: [{"id": 7, "fournisseur": INTERNET, "montant": "349.00"}],
}
BENEFICIAIRES = {
    1: [{"id": 1, "nom": "Fatima Lahlou", "rib_masque": "•••• 8633"}, {"id": 2, "nom": "Omar Benali", "rib_masque": "•••• 1120"}],
    3: [{"id": 5, "nom": "Fatima Lahlou", "rib_masque": "•••• 8633"}, {"id": 6, "nom": "Fatima Zahra Idrissi", "rib_masque": "•••• 4410"}],
}  # fmt: skip
PLAFONDS = {1: Decimal("10000.00"), 2: Decimal("5000.00"), 3: Decimal("2000.00")}


def refus(code, **details):
    return outils.RefusOutil({"code": code, "message": code, **details})


class FauxServeurMcp:
    """Doublure du serveur MCP (outils de paiement et de virement), avec les règles de la banque (solde, plafond)."""

    def __init__(self):
        self.soldes = {1: Decimal("2350.00"), 2: Decimal("150.00"), 3: Decimal("18500.00")}
        self.appels = []  # à la banque : (opération, client, facture ou bénéficiaire, montant, simulation)
        self.appels_mcp = []  # au serveur MCP : (outil, client, arguments, confirmation)

    @property
    def vrais_appels(self):
        return [appel for appel in self.appels if not appel[-1]]

    def appeler(self, client_id, nom, arguments, confirme=False):
        self.appels_mcp.append((nom, client_id, arguments, confirme))
        if nom == "payer_facture":
            return self._payer(client_id, arguments, simulation=not confirme)
        return self._virer(client_id, arguments, simulation=not confirme)

    def _verifier_solde(self, client_id, montant):
        if montant > self.soldes[client_id]:
            raise refus("solde_insuffisant", solde=f"{self.soldes[client_id]:.2f}", montant=f"{montant:.2f}")

    def _payer(self, client_id, arguments, simulation):
        factures = FACTURES.get(client_id, [])
        if "facture_id" in arguments:
            facture = next((f for f in factures if f["id"] == arguments["facture_id"]), None)
            if facture is None:
                raise refus("facture_introuvable")
        elif arguments.get("fournisseur") in FOURNISSEURS:
            nom = FOURNISSEURS[arguments["fournisseur"]]
            facture = next((f for f in factures if f["fournisseur"] == nom), None)
            if facture is None:
                raise refus("facture_absente", fournisseur=nom)
        else:
            raise refus("fournisseur_manquant")
        montant = Decimal(facture["montant"])
        self.appels.append(("paiement", client_id, facture["id"], montant, simulation))
        self._verifier_solde(client_id, montant)
        nouveau_solde = self.soldes[client_id] - montant
        if not simulation:
            self.soldes[client_id] = nouveau_solde
        return {
            **facture,
            "facture_id": facture["id"],
            "nouveau_solde": f"{nouveau_solde:.2f}",
            "simulation": simulation,
        }

    def _virer(self, client_id, arguments, simulation):
        beneficiaires = BENEFICIAIRES.get(client_id, [])
        if "beneficiaire_id" in arguments:
            candidats = [b for b in beneficiaires if b["id"] == arguments["beneficiaire_id"]]
        else:
            mots = str(arguments.get("beneficiaire") or "").lower().split()
            if not mots:
                raise refus("beneficiaire_manquant")
            candidats = [b for b in beneficiaires if set(mots) <= set(b["nom"].lower().split())]
            if len(candidats) > 1:
                raise refus("beneficiaire_ambigu", nom=arguments["beneficiaire"])
        if not candidats:
            raise refus("beneficiaire_inconnu", nom=arguments.get("beneficiaire", ""))
        try:
            montant = Decimal(str(arguments.get("montant")))
            valide = montant.is_finite() and montant > 0 and montant == montant.quantize(Decimal("0.01"))
        except InvalidOperation:
            valide = False
        if not valide:
            raise refus("montant_invalide")
        montant = montant.quantize(Decimal("0.01"))
        beneficiaire = candidats[0]
        self.appels.append(("virement", client_id, beneficiaire["id"], montant, simulation))
        if montant > PLAFONDS[client_id]:
            raise refus("plafond_depasse", plafond=f"{PLAFONDS[client_id]:.2f}", montant=f"{montant:.2f}")
        self._verifier_solde(client_id, montant)
        nouveau_solde = self.soldes[client_id] - montant
        if not simulation:
            self.soldes[client_id] = nouveau_solde
        return {
            "beneficiaire_id": beneficiaire["id"],
            "beneficiaire": beneficiaire["nom"],
            "beneficiaire_rib_masque": beneficiaire["rib_masque"],
            "montant": f"{montant:.2f}",
            "nouveau_solde": f"{nouveau_solde:.2f}",
            "simulation": simulation,
        }


@pytest.fixture
def fausse_banque_operations(monkeypatch):
    faux = FauxServeurMcp()
    monkeypatch.setattr(outils, "appeler", faux.appeler)
    return faux


@pytest.fixture
def ecrire():
    """Envoie un message dans une conversation (une neuve par test) et rend les événements SSE reçus.

    facture_id : clic sur « Payer avec Wakil » ; carte : clic sur « Oui » ou « Non » d'une carte précise."""
    conversation = str(uuid.uuid4())

    def envoyer(http, texte, conversation_id=conversation, **boutons):
        corps = {"conversation_id": conversation_id, "texte": texte, **boutons}
        return evenements(http.post("/chat", json=corps))

    return envoyer


def issue(evenements_recus):
    return next(donnees for nom, donnees in evenements_recus if nom == "reponse")["issue"]


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
            "issue": "faite",  # la carte passe à « Confirmé »
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


def test_beneficiaire_inconnu(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("faire_virement", {"beneficiaire": "Mehdi", "montant": 200})
    assert reponse(ecrire(salma, "sifet 200 l Mehdi")) == reponses.beneficiaire_inconnu("Mehdi")


def test_deux_beneficiaires_du_meme_prenom_on_demande_le_nom_complet(
    connecter, faux_llm, fausse_banque_operations, ecrire
):
    faux_llm("faire_virement", {"beneficiaire": "Fatima", "montant": 200})
    assert reponse(ecrire(connecter(3), "sifet 200 l Fatima")) == reponses.beneficiaire_ambigu("Fatima")


@pytest.mark.parametrize("montant", [0, -50, "bezaf", None])  # la lecture fine des montants : voir mcp-tools
def test_montant_absent_ou_invalide_on_demande_combien(salma, faux_llm, fausse_banque_operations, ecrire, montant):
    faux_llm("faire_virement", {"beneficiaire": "Fatima", "montant": montant})
    assert reponse(ecrire(salma, "sifet l Fatima")) == reponses.QUEL_MONTANT
    assert fausse_banque_operations.appels == []


def test_virement_au_dessus_du_plafond_refuse_d_avance(connecter, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("faire_virement", {"beneficiaire": "Fatima Lahlou", "montant": 3000})

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


# --- Boutons du front : « Payer avec Wakil » et les « Oui / Non » d'une carte ---------------------------------------


def test_le_bouton_payer_va_droit_a_la_carte_sans_le_llm(salma, faux_llm, fausse_banque_operations, ecrire):
    faux = faux_llm()  # un LLM qui ne comprendrait rien : il ne doit même pas être appelé

    recus = ecrire(salma, "Khelless liya la facture Internet (démo)", facture_id=2)

    carte = dict(recus)["confirmation"]
    assert (carte["fournisseur"], carte["montant"], carte["intro"]) == (INTERNET, "249.00", reponses.INTRO["paiement"])
    assert faux.appels == 0
    assert fausse_banque_operations.vrais_appels == []  # la confirmation reste obligatoire


@pytest.mark.parametrize("facture_id", [99, 7])  # 7 existe, mais c'est une facture de Youssef
def test_le_bouton_payer_refuse_une_facture_qui_n_est_pas_a_moi(
    salma, faux_llm, fausse_banque_operations, ecrire, facture_id
):
    faux_llm()
    assert reponse(ecrire(salma, "Khelless liya had l'facture", facture_id=facture_id)) == reponses.FACTURE_INTROUVABLE
    assert fausse_banque_operations.appels == []


def test_un_oui_sur_une_ancienne_carte_ne_confirme_pas_la_nouvelle(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm()
    carte_eau = dict(ecrire(salma, "Khelless liya l'eau", facture_id=1))["confirmation"]["carte"]
    carte_internet = dict(ecrire(salma, "Khelless liya internet", facture_id=2))["confirmation"]["carte"]

    # Clic sur « Oui » de la carte de l'eau, restée à l'écran : elle a été remplacée, rien ne doit partir
    recus = ecrire(salma, "Oui", carte=carte_eau)

    assert (reponse(recus), issue(recus)) == (reponses.CARTE_EXPIREE, "expiree")
    assert fausse_banque_operations.vrais_appels == []
    # La carte d'internet, elle, attend toujours : son propre « Oui » la paie
    assert issue(ecrire(salma, "Oui", carte=carte_internet)) == "faite"
    assert fausse_banque_operations.vrais_appels == [("paiement", 1, 2, Decimal("249.00"), False)]


def test_un_oui_sur_une_carte_deja_traitee_ne_fait_rien(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm()
    carte = dict(ecrire(salma, "Khelless liya l'eau", facture_id=1))["confirmation"]["carte"]
    assert issue(ecrire(salma, "Oui", carte=carte)) == "faite"

    assert issue(ecrire(salma, "Oui", carte=carte)) == "expiree"  # double clic : un seul paiement
    assert len(fausse_banque_operations.vrais_appels) == 1


@pytest.mark.parametrize(("reponse_client", "attendu"), [("La", "annulee"), ("ewa", "incomprise")])
def test_l_issue_indique_ce_qu_est_devenue_la_carte(
    salma, faux_llm, fausse_banque_operations, ecrire, reponse_client, attendu
):
    faux_llm()
    ecrire(salma, "Khelless liya l'eau", facture_id=1)
    assert issue(ecrire(salma, reponse_client)) == attendu


def test_le_oui_part_avec_la_confirmation_et_les_identifiants_exacts(salma, faux_llm, fausse_banque_operations, ecrire):
    faux_llm("faire_virement", {"beneficiaire": "fatima", "montant": 500})
    ecrire(salma, "sifet 500 DH l fatima")
    ecrire(salma, "Oui")

    assert fausse_banque_operations.appels_mcp == [
        ("faire_virement", 1, {"beneficiaire": "fatima", "montant": 500}, False),  # vérification à blanc
        ("faire_virement", 1, {"beneficiaire_id": 1, "montant": "500.00"}, True),  # le « oui » : la carte exacte
    ]
