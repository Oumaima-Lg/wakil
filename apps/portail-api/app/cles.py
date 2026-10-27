"""Génère la paire de clés des jetons de session (RS256), au format attendu dans .env : une ligne chacune.

Depuis apps/portail-api : uv run python -m app.cles >> ../../.env
La clé privée (WAKIL_JWT_CLE_PRIVEE) ne sert qu'à portail-api, qui signe les jetons. La clé publique
(WAKIL_JWT_CLE_PUBLIQUE) sert à agent-api, qui les vérifie. Ne jamais les commiter : .env est ignoré par Git.
"""

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generer() -> tuple[str, str]:
    """Une nouvelle paire (privée, publique). Le binaire de chaque clé (format DER) est écrit en base64."""
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
    print("\n# Clés des jetons de session (RS256), générées par apps/portail-api/app/cles.py")
    print(f"WAKIL_JWT_CLE_PRIVEE={privee}")
    print(f"WAKIL_JWT_CLE_PUBLIQUE={publique}")
