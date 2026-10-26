"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { lireEvenements } from "@/lib/sse";
import type { Facture } from "@/lib/types";

import { useEspace } from "./ContexteEspace";

/** Ce qu'est devenue une carte « Wach nconfirmi ? ». */
export type StatutCarte =
  | "attente" // les boutons Oui / Non sont actifs
  | "envoyee" // le client a répondu, la réponse est en route
  | "confirmee"
  | "annulee"
  | "refusee" // la banque a refusé au moment du « oui » (la situation avait changé)
  | "remplacee" // une demande plus récente l'a remplacée
  | "expiree" // le client a répondu à une carte qui n'attendait plus rien
  | "erreur"; // la banque n'a pas répondu après le « oui » : à vérifier dans les opérations

/** Une carte « Wach nconfirmi ? » : l'opération vérifiée à blanc par la banque, qui attend la réponse du client. */
export type Carte = {
  carte: string; // identifiant donné par le serveur : le bouton « Oui » le renvoie, pour confirmer CETTE opération
  type: "paiement" | "virement";
  intro: string;
  question: string;
  montant: string;
  nouveau_solde: string;
  fournisseur?: string;
  beneficiaire?: string;
  beneficiaire_rib_masque?: string;
  statut: StatutCarte;
};

/** Ce qu'est devenue l'opération, d'après le serveur (champ « issue » de l'événement reponse). */
type Issue = "faite" | "annulee" | "incomprise" | "refusee" | "erreur" | "expiree";
const STATUT_APRES: Record<Issue, StatutCarte> = {
  faite: "confirmee",
  annulee: "annulee",
  incomprise: "annulee",
  refusee: "refusee",
  erreur: "erreur",
  expiree: "expiree",
};

// Ce que le front sait d'un message. Les données viennent de la banque (via agent-api), jamais du LLM.
export type MessageClient = { id: string; auteur: "client"; texte: string };
export type MessageWakil = {
  id: string;
  auteur: "wakil";
  texte: string; // la référence : toujours affichable tel quel
  outil: string | null; // l'outil choisi, pour un affichage plus riche (solde en grand, opérations en tableau)
  donnees: unknown;
  erreur: boolean;
  issue?: Issue | null;
  carte?: Carte; // la carte « Wach nconfirmi ? », s'il y en a une
  demande?: Demande; // en cas d'erreur : la demande à renvoyer avec « Réessayer »
};
export type MessageChat = MessageClient | MessageWakil;

/** Où en est Wakil : il lit la demande (le LLM), puis interroge la banque. null : il attend un message. */
export type Avancement = "lecture" | "banque" | null;

/** Ce qui part vers /chat : le texte, et éventuellement le bouton cliqué (voir Message dans agent-api/app/main.py). */
type Demande = { texte: string; facture_id?: number; carte?: string };

// Les événements SSE envoyés par POST /chat (voir apps/agent-api/app/main.py).
type Evenement =
  | { nom: "etape"; donnees: { noeud: string; outil: string | null } }
  | {
      nom: "reponse";
      donnees: { texte: string; outil: string | null; donnees: unknown; erreur: boolean; issue: Issue | null };
    }
  | { nom: "erreur"; donnees: { texte: string } }
  | { nom: "confirmation"; donnees: Omit<Carte, "statut"> & { texte: string } }
  | { nom: "fin"; donnees: Record<string, never> };

const PANNE = "Smeh lia, Wakil ma khdamch daba. 3awed men ba3d.";
const EN_COURS: StatutCarte[] = ["attente", "envoyee"];

/** La conversation avec Wakil : les messages, l'envoi d'une demande et la lecture de la réponse en direct. */
export function useConversation() {
  const { recharger } = useEspace();
  // Un identifiant par visite de l'espace. Le serveur range la conversation sous « client:conversation ».
  // Tiré au premier message (dans un gestionnaire d'événement) et non au rendu : sinon Next le calculerait une fois
  // au pré-rendu du serveur, et tous les visiteurs partageraient le même.
  const conversationId = useRef<string | null>(null);
  const [messages, setMessages] = useState<MessageChat[]>([]);
  const [avancement, setAvancement] = useState<Avancement>(null);
  const [sessionExpiree, setSessionExpiree] = useState(false);
  // Le texte en cours de saisie, ici pour qu'un bouton d'une page puisse le préremplir (« Virer avec Wakil »).
  const [brouillon, setBrouillon] = useState("");
  const [curseur, setCurseur] = useState<{ position: number; jeton: number } | null>(null);
  const annulation = useRef<AbortController | null>(null);

  // Si le composant disparaît (déconnexion), on arrête de lire le flux en cours.
  useEffect(() => () => annulation.current?.abort(), []);

  const ajouter = useCallback((message: Omit<MessageClient, "id"> | Omit<MessageWakil, "id">) => {
    setMessages((liste) => [...liste, { ...message, id: crypto.randomUUID() } as MessageChat]);
  }, []);

  /** Change le statut des cartes choisies (sans toucher aux autres messages). */
  const changerCartes = useCallback((choisir: (carte: Carte) => boolean, statut: StatutCarte) => {
    setMessages((liste) =>
      liste.map((m) => (m.auteur === "wakil" && m.carte && choisir(m.carte) ? { ...m, carte: { ...m.carte, statut } } : m)),
    );
  }, []);

  const demander = useCallback(
    async (demande: Demande) => {
      setAvancement(demande.carte ? "banque" : "lecture"); // un « Oui » ne passe pas par le LLM
      const controleur = new AbortController();
      annulation.current = controleur;
      const panne = { auteur: "wakil", texte: PANNE, outil: null, donnees: null, erreur: true, demande } as const;
      // Si la réponse à une carte n'a pas pu partir, la carte redevient cliquable. Sans risque : le serveur
      // n'accepte un « Oui » que pour la carte qui attend vraiment, donc jamais deux fois le même paiement.
      const signalerPanne = () => {
        ajouter(panne);
        if (demande.carte) changerCartes((c) => c.carte === demande.carte && c.statut === "envoyee", "attente");
      };
      try {
        const reponse = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ conversation_id: (conversationId.current ??= crypto.randomUUID()), ...demande }),
          signal: controleur.signal,
        });
        if (reponse.status === 401) {
          setSessionExpiree(true); // session de 30 minutes terminée
          return;
        }
        if (!reponse.ok || !reponse.body) {
          signalerPanne();
          return;
        }
        let repondu = false;
        // for await : la boucle avance à chaque événement reçu, pendant que le serveur continue d'écrire.
        for await (const evenement of lireEvenements(reponse.body)) {
          const { nom, donnees } = evenement as Evenement;
          if (nom === "etape" && donnees.noeud === "comprendre" && donnees.outil) {
            setAvancement("banque"); // le LLM a choisi un outil : le code interroge la banque
          } else if (nom === "confirmation") {
            // Une nouvelle carte remplace celle qui attendait encore (le serveur l'a abandonnée)
            changerCartes((c) => EN_COURS.includes(c.statut), "remplacee");
            const { texte, ...carte } = donnees;
            ajouter({ auteur: "wakil", texte, outil: null, donnees: null, erreur: false, carte: { ...carte, statut: "attente" } });
            repondu = true;
          } else if (nom === "reponse") {
            const { issue } = donnees;
            if (issue === "expiree" && demande.carte) changerCartes((c) => c.carte === demande.carte, "expiree");
            else if (issue) changerCartes((c) => EN_COURS.includes(c.statut), STATUT_APRES[issue]);
            // « Réessayer » seulement pour une panne avant toute opération : après un « oui » sans réponse de la
            // banque, on ne sait pas si l'argent est parti, le client vérifie d'abord ses opérations.
            const reessayable = donnees.erreur && issue !== "erreur";
            ajouter({ auteur: "wakil", ...donnees, demande: reessayable ? demande : undefined });
            if (issue === "faite") void recharger(true); // l'espace se met à jour et surligne ce qui a changé
            repondu = true;
          } else if (nom === "erreur") {
            ajouter({ ...panne, texte: donnees.texte });
            repondu = true;
          }
        }
        if (!repondu) signalerPanne(); // flux coupé avant la réponse
      } catch {
        if (!controleur.signal.aborted) signalerPanne(); // réseau coupé, agent-api arrêté…
      } finally {
        setAvancement(null);
      }
    },
    [ajouter, changerCartes, recharger],
  );

  const occupe = avancement !== null || sessionExpiree;

  /** Envoie un nouveau message du client. */
  const envoyer = useCallback(
    (texte: string) => {
      const propre = texte.trim();
      if (!propre || occupe) return false;
      ajouter({ auteur: "client", texte: propre });
      void demander({ texte: propre });
      return true;
    },
    [ajouter, demander, occupe],
  );

  /** Boutons « Oui, confirmer » / « Non, annuler » d'une carte : la réponse vise CETTE carte, par son identifiant. */
  const repondreCarte = useCallback(
    (carte: Carte, reponse: "Oui" | "Non") => {
      if (occupe || carte.statut !== "attente") return;
      changerCartes((c) => c.carte === carte.carte, "envoyee");
      ajouter({ auteur: "client", texte: reponse });
      void demander({ texte: reponse, carte: carte.carte });
    },
    [ajouter, changerCartes, demander, occupe],
  );

  /** Bouton « Payer avec Wakil » d'une facture : l'intention est sûre, elle ne passe pas par le LLM. */
  const payerFacture = useCallback(
    (facture: Facture) => {
      if (occupe) return;
      const texte = `Khelless liya la facture ${facture.fournisseur}`;
      ajouter({ auteur: "client", texte });
      void demander({ texte, facture_id: facture.id });
    },
    [ajouter, demander, occupe],
  );

  /** Préremplit le champ de saisie et y place le curseur (« sifet | DH l Fatima Lahlou »). */
  const proposer = useCallback((texte: string, position = texte.length) => {
    setBrouillon(texte);
    setCurseur({ position, jeton: Date.now() });
  }, []);

  /** « Réessayer » : retire la bulle d'erreur et renvoie la même demande, sans la répéter dans la conversation. */
  const reessayer = useCallback(
    (erreur: MessageWakil) => {
      if (!erreur.demande || occupe) return;
      setMessages((liste) => liste.filter((m) => m.id !== erreur.id));
      if (erreur.demande.carte) changerCartes((c) => c.carte === erreur.demande?.carte, "envoyee");
      void demander(erreur.demande);
    },
    [changerCartes, demander, occupe],
  );

  return {
    messages,
    avancement,
    sessionExpiree,
    envoyer,
    reessayer,
    repondreCarte,
    payerFacture,
    brouillon,
    setBrouillon,
    proposer,
    curseur,
  };
}
