"""Captures d'écran de la démo pour le README : un Chrome sans fenêtre parcourt le site comme une visiteuse, avec la
cliente de démo Salma (données 100 % fictives), et enregistre les images dans ce dossier.

Le navigateur tourne dans le conteneur « navigateur » de docker-compose.yml (profil « captures ») et voit le site sur
son propre localhost:3000, relayé vers le conteneur du site. Ce script le pilote par le protocole DevTools de Chrome (port 9222). Il ne
confirme aucune opération : la carte « Wach nconfirmi ? » est photographiée puis annulée, la banque ne bouge pas.

Préparer (depuis la racine, Ollama démarré) : docker compose --profile images --profile captures up -d --build
Lancer (depuis apps/agent-api) :                 uv run python ../../docs/captures/capturer.py
"""

import asyncio
import base64
import itertools
import json
from pathlib import Path

import httpx
import websockets

ICI = Path(__file__).resolve().parent
NAVIGATEUR = "http://127.0.0.1:9222"
SITE = "http://localhost:3000"  # dans le conteneur du navigateur, relayé vers le site (docker-compose.yml)
ORDINATEUR = {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False}
TELEPHONE = {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True}
DELAI = 240  # secondes : le premier message recharge le modèle dans Ollama

# Les messages envoyés à Wakil, chacun en début de conversation : le LLM relit les messages précédents, et une
# question de FAQ posée juste après le solde part parfois vers le plafond (famille « suite » du benchmark).
SOLDE = "chhal f compte dyali ?"
QUESTION_FAQ = "ch7al kaykhlles l virement ?"
FACTURES = "bghit nchouf les factures dyali"

# En JavaScript, dans la page : la conversation, et « Wakil réfléchit encore ».
BULLES = "document.querySelectorAll('ol[aria-label=Conversation] > li')"
EN_COURS = f"[...{BULLES}].some(li => /Kanqra|Kanchouf|Kanqelleb/.test(li.textContent))"


def bouton(texte: str) -> str:
    """Le premier bouton visible dont le texte commence par `texte` (getClientRects : vide pour un élément caché, mais
    pas pour un bouton fixé à l'écran, dont offsetParent est toujours nul)."""
    return (
        "[...document.querySelectorAll('button')].find(b => b.getClientRects().length > 0"
        f" && b.textContent.trim().startsWith({json.dumps(texte)}))"
    )


class Onglet:
    """Un onglet de Chrome, piloté par le protocole DevTools (une commande JSON, une réponse)."""

    def __init__(self, connexion):
        self.connexion = connexion
        self.numeros = itertools.count(1)

    async def commande(self, methode: str, **parametres) -> dict:
        numero = next(self.numeros)
        await self.connexion.send(json.dumps({"id": numero, "method": methode, "params": parametres}))
        while True:  # les événements que Chrome envoie entre-temps sont ignorés
            message = json.loads(await self.connexion.recv())
            if message.get("id") == numero:
                if "error" in message:
                    raise RuntimeError(f"{methode} : {message['error']}")
                return message.get("result", {})

    async def js(self, code: str):
        resultat = await self.commande("Runtime.evaluate", expression=code, awaitPromise=True, returnByValue=True)
        return resultat.get("result", {}).get("value")

    async def attendre(self, condition: str, delai: float = DELAI) -> None:
        for _ in range(int(delai * 4)):
            if await self.js(f"Boolean({condition})"):
                return
            await asyncio.sleep(0.25)
        raise TimeoutError(f"Toujours faux après {delai} s : {condition}")

    async def ecran(self, appareil: dict) -> None:
        await self.commande("Emulation.setDeviceMetricsOverride", **appareil)
        await self.commande("Emulation.setScrollbarsHidden", hidden=True)  # des images sans barre de défilement

    async def aller(self, chemin: str) -> None:
        await self.commande("Page.navigate", url=SITE + chemin)
        await self.attendre("document.readyState === 'complete'")

    async def cliquer(self, element: str) -> None:
        await self.attendre(element)
        await self.js(f"({element}).click()")

    async def ecrire_a_wakil(self, texte: str) -> None:
        """Tape le message comme au clavier, l'envoie, puis attend la réponse de Wakil."""
        avant = await self.js(f"{BULLES}.length")
        await self.js("document.getElementById('message-wakil').focus()")
        await self.commande("Input.insertText", text=texte)
        await self.cliquer("document.querySelector('button[aria-label=Envoyer]:not([disabled])')")
        await self.attendre(f"{BULLES}.length >= {avant + 2} && !({EN_COURS})")

    async def photographier(self, nom: str) -> None:
        await asyncio.sleep(1)  # les transitions de l'interface se terminent
        image = await self.commande("Page.captureScreenshot", format="png")
        (ICI / f"{nom}.png").write_bytes(base64.b64decode(image["data"]))
        print(f"{nom}.png")


async def main() -> None:
    cible = httpx.put(f"{NAVIGATEUR}/json/new?about:blank").json()  # un onglet neuf, sans cookie
    async with websockets.connect(cible["webSocketDebuggerUrl"], max_size=None) as connexion:
        onglet = Onglet(connexion)
        await onglet.ecran(ORDINATEUR)

        # 1. L'accueil : le choix d'un client de démo
        await onglet.aller("/")
        await onglet.attendre(bouton("Ouvrir l'espace de Salma"))
        await onglet.photographier("accueil")

        # 2. L'espace bancaire de Salma
        await onglet.cliquer(bouton("Ouvrir l'espace de Salma"))
        await onglet.attendre("location.pathname === '/banque' && document.body.innerText.includes('DH')")
        await onglet.photographier("espace")

        # 3. Wakil cite la FAQ
        await onglet.cliquer(bouton("Wakil"))
        await onglet.ecrire_a_wakil(QUESTION_FAQ)
        await onglet.photographier("wakil-faq")

        # 4. Une nouvelle conversation (page rechargée) : le solde, puis un paiement à confirmer, page des factures
        await onglet.aller("/banque/factures")
        await onglet.cliquer(bouton("Wakil"))
        await onglet.ecrire_a_wakil(SOLDE)
        await onglet.cliquer(bouton("Payer avec Wakil"))
        await onglet.attendre(bouton("Oui, confirmer"))
        await onglet.js("document.querySelector('ol[aria-label=Conversation]').lastElementChild.scrollIntoView()")
        await onglet.photographier("wakil-confirmation")
        await onglet.cliquer(bouton("Non, annuler"))  # rien n'est payé
        await onglet.attendre(f"!({bouton('Oui, confirmer')})")

        # 5. Ma carte (Wakil refermé)
        await onglet.cliquer("document.querySelector('button[aria-label=\"Fermer Wakil\"]')")
        await onglet.cliquer("document.querySelector('a[href=\"/banque/carte\"]')")
        await onglet.attendre("location.pathname === '/banque/carte' && document.body.innerText.includes('Statut')")
        await onglet.photographier("carte")

        # 6. Sur téléphone : l'espace, puis Wakil en volet du bas
        await onglet.ecran(TELEPHONE)
        await onglet.aller("/banque")
        await onglet.attendre("document.body.innerText.includes('DH')")
        await onglet.photographier("telephone-espace")
        await onglet.cliquer("document.querySelector('button[aria-label^=\"Ouvrir Wakil\"]')")
        await onglet.ecrire_a_wakil(SOLDE)
        await onglet.ecrire_a_wakil(FACTURES)
        await onglet.photographier("telephone-wakil")

    httpx.get(f"{NAVIGATEUR}/json/close/{cible['id']}")


if __name__ == "__main__":
    asyncio.run(main())
