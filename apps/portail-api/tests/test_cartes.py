"""Tests des actions sur la carte : débloquer et faire opposition, depuis l'espace seulement."""

import pytest

from app import banque


@pytest.fixture
def actions(monkeypatch):
    """La banque, réduite à ce que ces routes lui demandent : on note chaque appel."""
    appels = []

    def debloquer(client_id, carte_id):
        appels.append(("deblocage", client_id, carte_id))
        if carte_id == 9:
            raise banque.RefusBanque(409, {"code": "carte_en_opposition", "message": "Définitif"})
        return {"id": carte_id, "numero_masque": "•••• 7919", "statut": "active"}

    def opposition(client_id, carte_id, motif):
        appels.append(("opposition", client_id, carte_id, motif))
        return {"id": carte_id, "numero_masque": "•••• 7919", "statut": "opposee", "motif_opposition": motif}

    def remplacer(client_id, carte_id):
        appels.append(("remplacement", client_id, carte_id))
        return {"id": 2, "numero_masque": "•••• 4200", "statut": "active", "remplacee_par": None}

    monkeypatch.setattr(banque, "debloquer_carte", debloquer)
    monkeypatch.setattr(banque, "faire_opposition", opposition)

    def bloquer(client_id, carte_id):
        appels.append(("blocage", client_id, carte_id))
        return {"id": carte_id, "numero_masque": "•••• 7919", "statut": "bloquee"}

    monkeypatch.setattr(banque, "remplacer_carte", remplacer)
    monkeypatch.setattr(banque, "bloquer_carte", bloquer)
    return appels


def test_debloquer_sa_carte(salma, actions):
    reponse = salma.post("/moi/cartes/1/deblocage")

    assert reponse.json()["statut"] == "active"
    assert actions == [("deblocage", 1, 1)]  # le client vient de la session


def test_faire_opposition_avec_un_motif(salma, actions):
    assert salma.post("/moi/cartes/1/opposition", json={"motif": "vol"}).json()["motif_opposition"] == "vol"


def test_un_motif_inconnu_est_refuse(salma, actions):
    assert salma.post("/moi/cartes/1/opposition", json={"motif": "ennui"}).status_code == 422
    assert actions == []


def test_le_refus_de_la_banque_arrive_au_front_avec_son_code(salma, actions):
    reponse = salma.post("/moi/cartes/9/deblocage")

    assert reponse.status_code == 409
    assert reponse.json()["detail"]["code"] == "carte_en_opposition"


def test_sans_session_rien_ne_part(api, actions):
    assert api.post("/moi/cartes/1/deblocage").status_code == 401
    assert actions == []


def test_commander_une_nouvelle_carte(salma, actions):
    assert salma.post("/moi/cartes/1/remplacement").json()["numero_masque"] == "•••• 4200"
    assert actions == [("remplacement", 1, 1)]


def test_bloquer_sa_carte_depuis_l_espace(salma, actions):
    assert salma.post("/moi/cartes/1/blocage").json()["statut"] == "bloquee"
    assert actions == [("blocage", 1, 1)]
