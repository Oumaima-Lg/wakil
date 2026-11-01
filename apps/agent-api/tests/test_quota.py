"""Tests du quota de messages : une fenêtre glissante par client, vérifiée après la session et avant le LLM."""

import uuid

import pytest

from app import quota, reponses


class Horloge:
    """Une horloge qu'on avance à la main, pour ne pas attendre une vraie minute."""

    def __init__(self):
        self.maintenant = 1000.0

    def __call__(self) -> float:
        return self.maintenant


def test_au_dela_du_quota_il_faut_attendre_que_le_plus_ancien_message_sorte_de_la_fenetre():
    horloge = Horloge()
    compteur = quota.Quota(3, fenetre=60, horloge=horloge)
    for _ in range(3):
        assert compteur.attente(1) == 0
        horloge.maintenant += 10  # messages à 1000, 1010 et 1020

    assert compteur.attente(1) == 30  # à 1030 : le message de 1000 sort de la fenêtre à 1060
    horloge.maintenant = 1060
    assert compteur.attente(1) == 0


def test_la_fenetre_glisse_pas_de_remise_a_zero_a_la_minute_pile():
    horloge = Horloge()
    compteur = quota.Quota(2, fenetre=60, horloge=horloge)
    horloge.maintenant = 1059  # deux messages juste avant « la minute »…
    assert compteur.attente(1) == compteur.attente(1) == 0

    horloge.maintenant = 1061  # … et deux secondes plus tard, toujours refusé
    assert compteur.attente(1) > 0


def test_un_refus_ne_compte_pas_et_chaque_client_a_son_quota():
    horloge = Horloge()
    compteur = quota.Quota(1, fenetre=60, horloge=horloge)
    compteur.attente(1)
    for _ in range(5):
        assert compteur.attente(1) > 0  # Salma attend…

    assert compteur.attente(2) == 0  # … pas Youssef
    horloge.maintenant += 60
    assert compteur.attente(1) == 0  # les refus n'ont pas allongé l'attente


@pytest.fixture
def quota_de_deux(monkeypatch):
    monkeypatch.setattr(quota, "quota", quota.Quota(2))


def test_le_message_de_trop_recoit_429_avec_le_delai_et_une_phrase_en_darija(salma, faux_llm, quota_de_deux):
    faux_llm(None)
    message = {"conversation_id": str(uuid.uuid4()), "texte": "salam"}

    statuts = [salma.post("/chat", json=message).status_code for _ in range(3)]
    reponse = salma.post("/chat", json=message)

    assert statuts == [200, 200, 429]
    assert reponse.json()["detail"] == reponses.TROP_DE_MESSAGES
    assert 0 < int(reponse.headers["retry-after"]) <= 60


def test_la_session_est_verifiee_avant_le_quota(api, connecter, quota_de_deux):
    youssef = connecter(2)
    for _ in range(3):
        assert api.post("/chat", json={"conversation_id": "x", "texte": "salam"}).status_code == 401  # pas compté
    assert youssef.post("/chat", json={"conversation_id": "x", "texte": "salam"}).status_code == 200
