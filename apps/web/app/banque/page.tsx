"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Montagnes } from "@/components/icones";

type Profil = { id: number; civilite: "madame" | "monsieur"; prenom: string; nom: string; ville: string };

/** Espace bancaire (version d'attente du morceau 7a) : vérifie la session, sinon retour à l'accueil. */
export default function Banque() {
  const router = useRouter();
  const [profil, setProfil] = useState<Profil | null>(null);

  useEffect(() => {
    // Le cookie de session part tout seul avec la requête : le JavaScript ne le lit jamais (HttpOnly).
    fetch("/api/moi")
      .then((reponse) => {
        if (reponse.status === 401) {
          router.replace("/");
          return null;
        }
        return reponse.json();
      })
      .then((donnees) => donnees && setProfil(donnees));
  }, [router]);

  async function seDeconnecter() {
    await fetch("/api/session", { method: "DELETE" });
    router.replace("/");
  }

  if (!profil) {
    return <p className="p-10 text-attenue">Chargement de votre espace…</p>;
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-16">
      <div className="flex items-center gap-3 text-accent">
        <Montagnes taille={30} />
        <span className="text-lg font-semibold tracking-wide text-texte">Banque Atlas Démo</span>
      </div>
      <h1 className="text-3xl font-semibold">
        Bonjour {profil.civilite === "madame" ? "Madame" : "Monsieur"} {profil.nom}
      </h1>
      <p className="text-attenue">
        Vous êtes connecté·e en tant que {profil.prenom} {profil.nom} ({profil.ville}). L&apos;espace bancaire complet
        arrive au morceau 7b.
      </p>
      <button
        type="button"
        onClick={seDeconnecter}
        className="self-start rounded-full border border-bordure-forte px-5 py-3 font-medium hover:border-accent"
      >
        Se déconnecter
      </button>
    </main>
  );
}
