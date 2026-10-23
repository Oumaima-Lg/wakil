"""Session du client de démo : un jeton signé (JWT) rangé dans un cookie que le JavaScript ne peut pas lire.

Équivalent Spring : Spring Security configuré en « resource server JWT ».
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException

COOKIE = "wakil_session"
DUREE = timedelta(minutes=30)
ALGORITHME = "HS256"
# « 1 » en ligne (HTTPS) : le cookie ne voyage alors jamais en clair. « 0 » sur ton PC (http://localhost).
COOKIE_SECURISE = os.environ.get("WAKIL_COOKIE_SECURISE", "0") == "1"

# Les seuls clients qu'on peut choisir sur l'écran d'accueil (données 100 % fictives).
CLIENTS_DEMO = {1: "Salma", 2: "Youssef", 3: "Nadia"}


def _cle() -> str:
    """La clé de signature vient de .env (plus tard d'Azure Key Vault), jamais du code."""
    return os.environ["WAKIL_JWT_SECRET"]


def creer_jeton(client_id: int, maintenant: datetime | None = None) -> str:
    maintenant = maintenant or datetime.now(UTC)
    contenu = {"sub": str(client_id), "iat": maintenant, "exp": maintenant + DUREE}
    return jwt.encode(contenu, _cle(), algorithm=ALGORITHME)


def client_connecte(wakil_session: Annotated[str | None, Cookie()] = None) -> int:
    """Lit le cookie de session et vérifie sa signature et son expiration. Sinon : 401."""
    if wakil_session is None:
        raise HTTPException(status_code=401, detail="Non connecté")
    try:
        # algorithms=[...] est obligatoire : sans lui, un jeton « alg: none » (non signé) pourrait passer.
        contenu = jwt.decode(wakil_session, _cle(), algorithms=[ALGORITHME])
    except jwt.InvalidTokenError:  # signature fausse, jeton expiré ou mal formé
        raise HTTPException(status_code=401, detail="Session invalide ou expirée") from None
    return int(contenu["sub"])


# Une route qui déclare ce paramètre ne peut pas oublier de vérifier la session.
ClientConnecte = Annotated[int, Depends(client_connecte)]
