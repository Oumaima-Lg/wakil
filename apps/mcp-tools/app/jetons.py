"""Les jetons de mcp-tools : il VÉRIFIE celui du client, et SIGNE le sien pour la banque.

- Le jeton du client : le jeton de session signé par portail-api, qu'agent-api relaie dans l'en-tête HTTP
  « Authorization: Bearer … ». mcp-tools le vérifie avec la clé publique de portail-api, et refuse un jeton qui ne le
  nomme pas dans « aud ». Le client vient de « sub » : personne ne peut plus se dire client n° 2 en écrivant un
  en-tête (c'était X-Client-Id jusqu'au 01/11/2026).
- Le jeton de la banque : mcp-tools ne retransmet jamais le jeton reçu (règle de la spécification MCP : un jeton ne
  sert qu'aux services qu'il nomme). Il signe son propre jeton, valable 60 secondes, destiné à bank-api seule.

Clés, une ligne chacune dans .env (format DER en base64) :
- WAKIL_JWT_CLE_PUBLIQUE : la clé publique de portail-api (déjà présente pour agent-api) ;
- MCP_JWT_CLE_PRIVEE : la clé privée de mcp-tools, qu'il est seul à avoir ; bank-api reçoit MCP_JWT_CLE_PUBLIQUE.
Pour les générer, depuis apps/mcp-tools : uv run python -m app.jetons >> ../../.env
"""

import base64
import os
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ALGORITHME = "RS256"
MOI = "mcp-tools"
PORTAIL = "portail-api"  # le seul émetteur des jetons de session
BANQUE = "bank-api"
DUREE = timedelta(seconds=60)  # le temps d'un appel : un jeton volé dans un journal ne sert presque à rien


class JetonInvalide(Exception):
    """Jeton absent, signé par une autre clé, expiré, ou destiné à un autre service."""


def client_du_jeton(authorization: str | None) -> int:
    """Le client du jeton relayé par agent-api, après vérification de la signature, de l'émetteur, du destinataire et
    de l'expiration."""
    if not authorization or not authorization.startswith("Bearer "):
        raise JetonInvalide("le jeton du client manque")
    try:
        contenu = jwt.decode(
            authorization.removeprefix("Bearer "),
            _cle_publique_du_portail(),
            algorithms=[ALGORITHME],  # jamais « alg: none », ni un HS256 signé avec la clé publique
            issuer=PORTAIL,
            audience=MOI,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
        return int(contenu["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise JetonInvalide("jeton du client invalide ou expiré") from None


def jeton_pour_la_banque(client_id: int, maintenant: datetime | None = None) -> str:
    maintenant = maintenant or datetime.now(UTC)
    contenu = {"sub": str(client_id), "iss": MOI, "aud": BANQUE, "iat": maintenant, "exp": maintenant + DUREE}
    return jwt.encode(contenu, _cle_privee(), algorithm=ALGORITHME)


def _cle_publique_du_portail():
    return serialization.load_der_public_key(base64.b64decode(os.environ["WAKIL_JWT_CLE_PUBLIQUE"]))


def _cle_privee():
    return serialization.load_der_private_key(base64.b64decode(os.environ["MCP_JWT_CLE_PRIVEE"]), password=None)


def generer() -> tuple[str, str]:
    """Une nouvelle paire (privée, publique), comme apps/portail-api/app/cles.py."""
    cle = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    privee = cle.private_bytes(
        serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    publique = cle.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return base64.b64encode(privee).decode(), base64.b64encode(publique).decode()


if __name__ == "__main__":
    privee, publique = generer()
    # La ligne vide d'abord : si .env ne finit pas par un retour à la ligne, la clé ne se colle pas à la dernière valeur.
    print("\n# Clés des jetons de mcp-tools vers bank-api (RS256), générées par apps/mcp-tools/app/jetons.py")
    print(f"MCP_JWT_CLE_PRIVEE={privee}")
    print(f"MCP_JWT_CLE_PUBLIQUE={publique}")
