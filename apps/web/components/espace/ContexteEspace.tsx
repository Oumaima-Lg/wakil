"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useState } from "react";

import type { Espace } from "@/lib/types";

type ValeurEspace = {
  espace: Espace | null;
  erreur: string | null;
  /** Relit le compte dans la banque : utile après une opération faite avec Wakil (étape S3). */
  recharger: () => Promise<void>;
  wakilOuvert: boolean;
  setWakilOuvert: (ouvert: boolean) => void;
};

const Contexte = createContext<ValeurEspace | null>(null);

/** Les données de l'espace, partagées par toutes les pages /banque/… (comme un service injecté en Angular). */
export function useEspace(): ValeurEspace {
  const valeur = useContext(Contexte);
  if (!valeur) throw new Error("useEspace doit être utilisé dans <FournisseurEspace>");
  return valeur;
}

type Resultat = { espace: Espace } | { erreur: string } | "sans-session";

/** Lit l'espace du client connecté. Le cookie de session part tout seul : le JavaScript ne le lit jamais (HttpOnly). */
async function lireEspace(): Promise<Resultat> {
  const reponse = await fetch("/api/moi/espace").catch(() => null); // null : réseau coupé
  if (reponse?.status === 401) return "sans-session";
  if (!reponse?.ok) return { erreur: "La banque de démo est momentanément indisponible. Réessayez dans un instant." };
  return { espace: await reponse.json() };
}

export function FournisseurEspace({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [espace, setEspace] = useState<Espace | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [wakilOuvert, setWakilOuvert] = useState(false); // fermé au départ : bouton flottant « Wakil »

  const appliquer = useCallback(
    (resultat: Resultat) => {
      if (resultat === "sans-session") {
        router.replace("/"); // pas (ou plus) de session : retour à l'accueil
      } else if ("erreur" in resultat) {
        setErreur(resultat.erreur);
      } else {
        setEspace(resultat.espace);
        setErreur(null);
      }
    },
    [router],
  );

  const recharger = useCallback(async () => appliquer(await lireEspace()), [appliquer]);

  useEffect(() => {
    // L'état change dans le .then, une fois la réponse arrivée (et non pendant l'effet lui-même)
    lireEspace().then(appliquer);
  }, [appliquer]);

  // Quand on quitte l'espace (déconnexion, retour à l'accueil), Next le garde en mémoire, masqué (React <Activity>).
  // On efface alors le compte et, avec lui, la conversation (le panneau Wakil disparaît) : le client suivant ne les
  // verra jamais, même un instant. À son retour, l'effet ci-dessus relit l'espace de celui qui est connecté.
  useLayoutEffect(
    () => () => {
      setEspace(null);
      setErreur(null);
    },
    [],
  );

  return (
    <Contexte.Provider value={{ espace, erreur, recharger, wakilOuvert, setWakilOuvert }}>{children}</Contexte.Provider>
  );
}
