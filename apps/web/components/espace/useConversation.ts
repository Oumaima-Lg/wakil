"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { lireEvenements } from "@/lib/sse";

// Ce que le front sait d'un message. Les données viennent de la banque (via agent-api), jamais du LLM.
export type MessageClient = { id: string; auteur: "client"; texte: string };
export type MessageWakil = {
  id: string;
  auteur: "wakil";
  texte: string; // la référence : toujours affichable tel quel
  outil: string | null; // l'outil choisi, pour un affichage plus riche (solde en grand, opérations en tableau)
  donnees: unknown;
  erreur: boolean;
  demande?: string; // en cas d'erreur : la demande à renvoyer avec « Réessayer »
};
export type MessageChat = MessageClient | MessageWakil;

/** Où en est Wakil : il lit la demande (le LLM), puis interroge la banque. null : il attend un message. */
export type Avancement = "lecture" | "banque" | null;

// Les événements SSE envoyés par POST /chat (voir apps/agent-api/app/main.py).
type Evenement =
  | { nom: "etape"; donnees: { noeud: string; outil: string | null } }
  | { nom: "reponse"; donnees: { texte: string; outil: string | null; donnees: unknown; erreur: boolean } }
  | { nom: "erreur"; donnees: { texte: string } }
  // Paiement ou virement vérifié à blanc : le graphe attend « oui » ou « la » (la carte arrive au morceau 11)
  | { nom: "confirmation"; donnees: { texte: string; type: "paiement" | "virement" } }
  | { nom: "fin"; donnees: Record<string, never> };

const PANNE = "Smeh lia, Wakil ma khdamch daba. 3awed men ba3d.";

/** La conversation avec Wakil : les messages, l'envoi d'une demande et la lecture de la réponse en direct. */
export function useConversation() {
  // Un identifiant par visite de l'espace. Le serveur range la conversation sous « client:conversation ».
  const [conversationId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<MessageChat[]>([]);
  const [avancement, setAvancement] = useState<Avancement>(null);
  const [sessionExpiree, setSessionExpiree] = useState(false);
  const annulation = useRef<AbortController | null>(null);

  // Si le composant disparaît (déconnexion), on arrête de lire le flux en cours.
  useEffect(() => () => annulation.current?.abort(), []);

  const ajouter = useCallback((message: Omit<MessageClient, "id"> | Omit<MessageWakil, "id">) => {
    setMessages((liste) => [...liste, { ...message, id: crypto.randomUUID() } as MessageChat]);
  }, []);

  const demander = useCallback(
    async (texte: string) => {
      setAvancement("lecture");
      const controleur = new AbortController();
      annulation.current = controleur;
      const panne = { auteur: "wakil", texte: PANNE, outil: null, donnees: null, erreur: true, demande: texte } as const;
      try {
        const reponse = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ conversation_id: conversationId, texte }),
          signal: controleur.signal,
        });
        if (reponse.status === 401) {
          setSessionExpiree(true); // session de 30 minutes terminée
          return;
        }
        if (!reponse.ok || !reponse.body) {
          ajouter(panne);
          return;
        }
        let repondu = false;
        // for await : la boucle avance à chaque événement reçu, pendant que le serveur continue d'écrire.
        for await (const evenement of lireEvenements(reponse.body)) {
          const { nom, donnees } = evenement as Evenement;
          if (nom === "etape" && donnees.noeud === "comprendre" && donnees.outil) {
            setAvancement("banque"); // le LLM a choisi un outil : le code interroge la banque
          } else if (nom === "reponse") {
            ajouter({ auteur: "wakil", ...donnees, demande: donnees.erreur ? texte : undefined });
            repondu = true;
          } else if (nom === "confirmation") {
            ajouter({ auteur: "wakil", texte: donnees.texte, outil: "confirmation", donnees, erreur: false });
            repondu = true;
          } else if (nom === "erreur") {
            ajouter({ ...panne, texte: donnees.texte });
            repondu = true;
          }
        }
        if (!repondu) ajouter(panne); // flux coupé avant la réponse
      } catch {
        if (!controleur.signal.aborted) ajouter(panne); // réseau coupé, agent-api arrêté…
      } finally {
        setAvancement(null);
      }
    },
    [ajouter, conversationId],
  );

  /** Envoie un nouveau message du client. */
  const envoyer = useCallback(
    (texte: string) => {
      const propre = texte.trim();
      if (!propre || avancement || sessionExpiree) return false;
      ajouter({ auteur: "client", texte: propre });
      void demander(propre);
      return true;
    },
    [ajouter, avancement, demander, sessionExpiree],
  );

  /** « Réessayer » : retire la bulle d'erreur et renvoie la même demande, sans la répéter dans la conversation. */
  const reessayer = useCallback(
    (erreur: MessageWakil) => {
      if (!erreur.demande || avancement) return;
      setMessages((liste) => liste.filter((m) => m.id !== erreur.id));
      void demander(erreur.demande);
    },
    [avancement, demander],
  );

  return { messages, avancement, sessionExpiree, envoyer, reessayer };
}
