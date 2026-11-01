"""Quota de messages par client : au plus WAKIL_QUOTA_MESSAGES messages (20 par défaut) sur les 60 dernières secondes,
sinon 429 « Too Many Requests ».

Contre la consommation sans limite (OWASP LLM10) : chaque message peut faire travailler le LLM, et un client, ou un
script qui a son cookie, ne doit pas occuper Ollama pour tous les autres. Une personne qui écrit ne dépasse pas 20
messages par minute ; la rafale de 30 messages du rapport de sécurité, si.

Fenêtre glissante : on garde l'heure des derniers messages de chaque client et on compte ceux des 60 dernières secondes
(pas de « remise à zéro à la minute pile », qui laisserait passer 40 messages en 2 secondes à cheval sur deux minutes).
Le compteur vit dans la mémoire du processus : c'est suffisant pour une seule instance d'agent-api. Avec plusieurs
répliques (S6), il faudra un compteur partagé, ou le quota de la passerelle.
"""

import math
import os
import threading
import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import Depends, HTTPException

from app import reponses
from app.session import ClientConnecte

FENETRE = 60.0  # secondes


class Quota:
    def __init__(self, messages: int, fenetre: float = FENETRE, horloge=time.monotonic):
        self.messages, self.fenetre, self.horloge = messages, fenetre, horloge
        self.recus: dict[int, deque[float]] = defaultdict(deque)  # client → heures de ses derniers messages
        self.verrou = threading.Lock()  # FastAPI traite plusieurs requêtes en même temps

    def attente(self, client_id: int) -> float:
        """0 si le message est accepté (et compté) ; sinon, les secondes à attendre avant le prochain."""
        with self.verrou:
            maintenant = self.horloge()
            recus = self.recus[client_id]
            while recus and recus[0] <= maintenant - self.fenetre:
                recus.popleft()
            if len(recus) >= self.messages:
                return recus[0] + self.fenetre - maintenant
            recus.append(maintenant)
            return 0.0


quota = Quota(int(os.environ.get("WAKIL_QUOTA_MESSAGES", "20")))


def dans_le_quota(client_id: ClientConnecte) -> int:
    """La session d'abord (401), puis le quota (429), avant que le message n'atteigne le LLM."""
    attente = quota.attente(client_id)
    if attente:
        raise HTTPException(
            status_code=429,
            detail=reponses.TROP_DE_MESSAGES,
            headers={"Retry-After": str(math.ceil(attente))},
        )
    return client_id


# À la place de ClientConnecte sur une route qui fait travailler le LLM.
ClientDansLeQuota = Annotated[int, Depends(dans_le_quota)]
