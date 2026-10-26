"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useRef, useState } from "react";

import { AUCUNE_NOUVEAUTE, differences, type Nouveautes } from "@/lib/espace";
import type { Espace } from "@/lib/types";

type ValeurEspace = {
  espace: Espace | null;
  erreur: string | null;
  /** Relit le compte dans la banque. surligner : après une opération faite avec Wakil, on repère ce qui a changé. */
  recharger: (surligner?: boolean) => Promise<void>;
  /** Ce qui a changé après la dernière opération de Wakil : surligné « Nouveau », « à l'instant ». */
  nouveautes: Nouveautes;
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
  const [nouveautes, setNouveautes] = useState<Nouveautes>(AUCUNE_NOUVEAUTE);
  const precedent = useRef<Espace | null>(null); // le compte tel qu'il était avant le dernier rechargement

  const appliquer = useCallback(
    (resultat: Resultat, surligner = false) => {
      if (resultat === "sans-session") {
        router.replace("/"); // pas (ou plus) de session : retour à l'accueil
      } else if ("erreur" in resultat) {
        setErreur(resultat.erreur);
      } else {
        if (surligner && precedent.current) setNouveautes(differences(precedent.current, resultat.espace));
        precedent.current = resultat.espace;
        setEspace(resultat.espace);
        setErreur(null);
      }
    },
    [router],
  );

  const recharger = useCallback(
    async (surligner = false) => appliquer(await lireEspace(), surligner),
    [appliquer],
  );

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
      setNouveautes(AUCUNE_NOUVEAUTE);
      precedent.current = null;
    },
    [],
  );

  return (
    <Contexte.Provider value={{ espace, erreur, recharger, nouveautes, wakilOuvert, setWakilOuvert }}>
      {children}
    </Contexte.Provider>
  );
}
