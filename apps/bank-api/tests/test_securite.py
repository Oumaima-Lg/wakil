"""Tests du contrôle d'accès : seul un jeton signé par mcp-tools ou portail-api, destiné à bank-api et encore valide,
dit quel client appelle. L'ancien en-tête X-Client-Id ne suffit plus."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from conftest import CLES, entetes, jeton, nouvelle_cle


@pytest.mark.parametrize("emetteur", ["mcp-tools", "portail-api"])
def test_un_jeton_d_un_emetteur_de_confiance_donne_le_client(api, emetteur):
    reponse = api.get("/comptes/2/solde", headers=entetes(2, emetteur=emetteur))

    assert reponse.status_code == 200
    assert reponse.json()["solde"] == "150.00"


@pytest.mark.parametrize(
    "entete",
    [
        {"X-Client-Id": "2"},  # n'importe qui peut écrire un en-tête
        {"Authorization": f"Bearer {jeton(2, cle=nouvelle_cle())}"},  # signé par une clé inventée
        {"Authorization": f"Bearer {jeton(2, cle=CLES['portail-api'], iss='mcp-tools')}"},  # se dit mcp-tools
        {"Authorization": f"Bearer {jeton(2, emetteur='agent-api', cle=nouvelle_cle())}"},  # émetteur inconnu
        {"Authorization": f"Bearer {jeton(2, aud=['portail-api', 'agent-api', 'mcp-tools'])}"},  # jeton de session
        {"Authorization": f"Bearer {jeton(2, exp=datetime.now(UTC) - timedelta(seconds=1))}"},  # expiré
        {"Authorization": "Bearer " + jwt.encode({"sub": "2", "iss": "mcp-tools", "aud": "bank-api"}, None, "none")},
        {"Authorization": "Bearer pas-un-jeton"},
    ],
    ids=[
        "x-client-id",
        "cle-inventee",
        "faux-emetteur",
        "emetteur-inconnu",
        "jeton-de-session",
        "expire",
        "alg-none",
        "illisible",
    ],  # fmt: skip
)
def test_un_jeton_qui_ne_prouve_rien_est_refuse(api, entete):
    reponse = api.get("/comptes/2/solde", headers=entete)

    assert reponse.status_code == 401
    assert reponse.headers["www-authenticate"] == "Bearer"
