"use client";

import { useState } from "react";

import { FournisseurEspace, useEspace } from "@/components/espace/ContexteEspace";
import { Menu } from "@/components/espace/Menu";
import { PanneauWakil } from "@/components/espace/PanneauWakil";

/**
 * Cadre commun à toutes les pages /banque/… (≈ un composant parent avec <router-outlet> en Angular) :
 * le menu, le panneau Wakil et les données du compte restent en place, seul {children} change.
 */
export default function LayoutBanque({ children }: LayoutProps<"/banque">) {
  return (
    <FournisseurEspace>
      <Coquille>{children}</Coquille>
    </FournisseurEspace>
  );
}

function Coquille({ children }: { children: React.ReactNode }) {
  const { espace, erreur, wakilOuvert } = useEspace();
  const [menuOuvert, setMenuOuvert] = useState(false); // réduit au départ : colonne d'icônes

  if (erreur) {
    return (
      <p role="alert" className="m-10 rounded-2xl border border-bordure bg-surface p-6 text-attenue">
        {erreur}
      </p>
    );
  }
  // data-coquille fixe la hauteur de la page à celle de l'écran (globals.css) : seul <main> défile.
  // {children} est toujours rendu (chaque page attend le compte elle-même) : Next peut ainsi valider les pages.
  return (
    <div data-coquille className="flex min-h-0 flex-1">
      {espace && <Menu espace={espace} ouvert={menuOuvert} basculer={() => setMenuOuvert(!menuOuvert)} />}
      {/* Wakil fermé : plus de marge en bas, pour que le bouton flottant ne cache pas la fin du contenu */}
      <main
        className={`flex min-w-0 flex-1 flex-col gap-6 overflow-y-auto px-8.5 pt-7 ${wakilOuvert ? "pb-12" : "pb-28"}`}
      >
        {!espace && <p className="text-attenue">Chargement de votre espace…</p>}
        {children}
      </main>
      {espace && <PanneauWakil />}
    </div>
  );
}
