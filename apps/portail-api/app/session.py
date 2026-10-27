"""Session du client de démo : portail-api CRÉE le jeton signé (JWT) et le range dans un cookie que le JavaScript ne
peut pas lire.

RS256 : le jeton est signé avec la clé privée, que seul portail-api possède. agent-api le vérifie avec la clé publique :
il peut s'assurer qu'un jeton vient d'ici, mais jamais en fabriquer un.
Équivalent Spring : le serveur d'autorisation (Keycloak, Spring Authorization Server) qui émet les jetons.
"""

import base64
import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from cryptography.hazmat.primitives import serialization
from fastapi import Cookie, Depends, HTTPException

COOKIE = "wakil_session"
DUREE = timedelta(minutes=30)
ALGORITHME = "RS256"
EMETTEUR = "portail-api"  # « iss » : qui a créé le jeton
MOI = "portail-api"
# « aud » : les services à qui le jeton est destiné. Chacun refuse un jeton qui ne le nomme pas.
DESTINATAIRES = ["portail-api", "agent-api"]
# « 1 » en ligne (HTTPS) : le cookie ne voyage alors jamais en clair. « 0 » sur ton PC (http://localhost).
COOKIE_SECURISE = os.environ.get("WAKIL_COOKIE_SECURISE", "0") == "1"

# Les seuls clients qu'on peut choisir sur l'écran d'accueil (données 100 % fictives).
CLIENTS_DEMO = {1: "Cas normal", 2: "Solde insuffisant", 3: "Plafond de virement bas"}  # id → scénario testé


def _cle_privee():
    """La clé privée vient de .env (plus tard d'Azure Key Vault), jamais du code. Elle y tient sur une ligne : le
    binaire de la clé (format DER) écrit en base64. Pour la générer : voir app/cles.py."""
    return serialization.load_der_private_key(base64.b64decode(os.environ["WAKIL_JWT_CLE_PRIVEE"]), password=None)


def creer_jeton(client_id: int, maintenant: datetime | None = None) -> str:
    maintenant = maintenant or datetime.now(UTC)
    contenu = {
        "sub": str(client_id),
        "iss": EMETTEUR,
        "aud": DESTINATAIRES,
        "iat": maintenant,
        "exp": maintenant + DUREE,
    }
    return jwt.encode(contenu, _cle_privee(), algorithm=ALGORITHME)


def client_connecte(wakil_session: Annotated[str | None, Cookie()] = None) -> int:
    """Lit le cookie de session et vérifie sa signature, son émetteur, son destinataire et son expiration. Sinon : 401."""
    if wakil_session is None:
        raise HTTPException(status_code=401, detail="Non connecté")
    try:
        contenu = jwt.decode(
            wakil_session,
            _cle_privee().public_key(),  # vérifier ne demande que la clé publique
            # algorithms=[...] est obligatoire : sans lui, un jeton « alg: none » (non signé) pourrait passer.
            algorithms=[ALGORITHME],
            issuer=EMETTEUR,
            audience=MOI,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
    except jwt.InvalidTokenError:  # signature fausse, jeton expiré, mal formé, ou destiné à un autre service
        raise HTTPException(status_code=401, detail="Session invalide ou expirée") from None
    return int(contenu["sub"])


# Une route qui déclare ce paramètre ne peut pas oublier de vérifier la session.
ClientConnecte = Annotated[int, Depends(client_connecte)]
