"""Contrôle d'accès de bank-api : QUI appelle, pour quel client (un jeton signé), puis À QUOI il a droit (ses comptes).

bank-api est un service interne. Deux services l'appellent, chacun avec un jeton court (60 s) signé de sa propre clé
privée, pour un client précis (« sub ») et destiné à bank-api (« aud ») :
- mcp-tools, la seule porte de l'IA vers la banque (clé publique : MCP_JWT_CLE_PUBLIQUE) ;
- portail-api, pour les pages de l'espace (clé publique : WAKIL_JWT_CLE_PUBLIQUE).
bank-api n'a que les clés publiques : elle vérifie, elle ne fabrique jamais de jeton. Jusqu'au 01/11/2026, elle
croyait l'en-tête X-Client-Id sur parole (attaques « banque-… » du rapport de sécurité). À ajouter en S6 : bank-api
joignable seulement depuis l'intérieur (ingress interne). Équivalent Spring : un « resource server JWT » avec deux
émetteurs de confiance.
"""

import base64
import os
from typing import Annotated

import jwt
from cryptography.hazmat.primitives import serialization
from fastapi import Depends, Header, HTTPException

from app.db import Connexion

MOI = "bank-api"
# Les émetteurs de confiance, et la variable d'environnement de la clé publique de chacun.
EMETTEURS = {"mcp-tools": "MCP_JWT_CLE_PUBLIQUE", "portail-api": "WAKIL_JWT_CLE_PUBLIQUE"}


def _refus(detail: str) -> HTTPException:
    return HTTPException(status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def client_connecte(authorization: Annotated[str | None, Header()] = None) -> int:
    """Le client du jeton « Authorization: Bearer … », après vérification de la signature, de l'émetteur, du
    destinataire et de l'expiration. Sinon : 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise _refus("Jeton manquant")
    jeton = authorization.removeprefix("Bearer ")
    try:
        # L'émetteur annoncé sert seulement à choisir la clé : la vérification qui suit exige que le jeton soit
        # signé par la clé de CET émetteur. Se dire « mcp-tools » sans sa clé privée ne mène à rien.
        emetteur = jwt.decode(jeton, options={"verify_signature": False}).get("iss")
        if emetteur not in EMETTEURS:
            raise _refus("Émetteur inconnu")
        cle = serialization.load_der_public_key(base64.b64decode(os.environ[EMETTEURS[emetteur]]))
        contenu = jwt.decode(
            jeton,
            cle,
            algorithms=["RS256"],  # jamais « alg: none », ni un HS256 signé avec la clé publique
            issuer=emetteur,
            audience=MOI,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
        return int(contenu["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise _refus("Jeton invalide ou expiré") from None


# Raccourci à mettre dans la signature d'une route pour recevoir l'id du client connecté.
ClientConnecte = Annotated[int, Depends(client_connecte)]


def compte_du_client(compte_id: int, client_id: ClientConnecte, conn: Connexion) -> dict:
    """Le compte {compte_id} de l'URL, s'il appartient au client connecté. Sinon : 404."""
    compte = conn.execute(
        "SELECT id, solde FROM comptes WHERE id = %s AND client_id = %s",
        (compte_id, client_id),
    ).fetchone()
    if compte is None:
        # 404 et pas 403 : on ne révèle pas qu'un compte existe chez un autre client.
        raise HTTPException(status_code=404, detail="Compte introuvable")
    return compte


# Une route qui déclare ce paramètre ne peut pas oublier le contrôle d'accès : FastAPI le fait avant elle.
CompteDuClient = Annotated[dict, Depends(compte_du_client)]
