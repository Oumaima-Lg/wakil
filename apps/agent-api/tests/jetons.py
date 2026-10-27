"""Des jetons de session de test, signés comme portail-api les signe (RS256), avec une paire de clés de test.

agent-api n'a que la clé publique : ici, les tests jouent le rôle de portail-api, qui a la clé privée.
"""

import base64
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

CLE_PRIVEE = rsa.generate_private_key(public_exponent=65537, key_size=2048)  # tirée à chaque lancement des tests
CLE_PUBLIQUE_DER = CLE_PRIVEE.public_key().public_bytes(
    serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
)
CLE_PUBLIQUE = base64.b64encode(CLE_PUBLIQUE_DER).decode()  # telle qu'elle est rangée dans .env


def jeton(client_id: int = 1, cle=CLE_PRIVEE, algorithme: str = "RS256", **changements) -> str:
    """Un jeton comme ceux de portail-api. changements remplace un champ, ou le retire s'il vaut None."""
    maintenant = datetime.now(UTC)
    contenu = {
        "sub": str(client_id),
        "iss": "portail-api",
        "aud": ["portail-api", "agent-api"],
        "iat": maintenant,
        "exp": maintenant + timedelta(minutes=30),
        **changements,
    }
    return jwt.encode({k: v for k, v in contenu.items() if v is not None}, cle, algorithm=algorithme)
