"use client";

import { createContext, useContext } from "react";

import { useConversation } from "./useConversation";

type ValeurConversation = ReturnType<typeof useConversation>;

const Contexte = createContext<ValeurConversation | null>(null);

/**
 * La conversation avec Wakil, partagée par le panneau et par les pages : un bouton « Payer avec Wakil » d'une page
 * peut ainsi envoyer une demande dans le panneau (comme un service injecté en Angular).
 */
export function FournisseurConversation({ children }: { children: React.ReactNode }) {
  return <Contexte.Provider value={useConversation()}>{children}</Contexte.Provider>;
}

export function useWakil(): ValeurConversation {
  const valeur = useContext(Contexte);
  if (!valeur) throw new Error("useWakil doit être utilisé dans <FournisseurConversation>");
  return valeur;
}
