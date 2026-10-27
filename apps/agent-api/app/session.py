"""Vérification de la session : agent-api lit le jeton signé que portail-api a rangé dans le cookie.

RS256 : agent-api n'a que la clé publique. Il peut vérifier qu'un jeton vient bien de portail-api, mais jamais en
fabriquer un : même si quelqu'un prenait le contrôle d'agent-api, il ne pourrait pas se faire passer pour un autre
client ailleurs. Équivalent Spring : un « resource server JWT » configuré avec la clé publique de l'émetteur.
"""

import base64
import os
from typing import Annotated

import jwt
from cryptography.hazmat.primitives import serialization
from fastapi import Cookie, Depends, HTTPException

COOKIE = "wakil_session"
ALGORITHME = "RS256"
EMETTEUR = "portail-api"  # « iss » : seul portail-api crée des jetons
MOI = "agent-api"  # « aud » : un jeton qui n'est pas destiné à agent-api est refusé


def _cle_publique():
    """La clé publique de portail-api vient de .env (plus tard d'Azure Key Vault). Elle y tient sur une ligne : le
    binaire de la clé (format DER) écrit en base64."""
    return serialization.load_der_public_key(base64.b64decode(os.environ["WAKIL_JWT_CLE_PUBLIQUE"]))


def client_connecte(wakil_session: Annotated[str | None, Cookie()] = None) -> int:
    """Lit le cookie de session et vérifie sa signature, son émetteur, son destinataire et son expiration. Sinon : 401."""
    if wakil_session is None:
        raise HTTPException(status_code=401, detail="Non connecté")
    try:
        contenu = jwt.decode(
            wakil_session,
            _cle_publique(),
            # algorithms=[...] est obligatoire : sans lui, un jeton « alg: none » (non signé) pourrait passer, ou un
            # jeton HS256 signé avec la clé publique, que tout le monde peut connaître.
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
