"use client";

import { useCallback, useState } from "react";

import { FournisseurConversation } from "@/components/espace/ContexteConversation";
import { FournisseurEspace, useEspace } from "@/components/espace/ContexteEspace";
import { Menu, MenuMobile } from "@/components/espace/Menu";
import { BarreBas, EnTeteMobile } from "@/components/espace/NavigationMobile";
import { PanneauWakil } from "@/components/espace/PanneauWakil";
import { useEcranLarge } from "@/lib/useEcranLarge";

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
  const ecranLarge = useEcranLarge();
  const [menuOuvert, setMenuOuvert] = useState(false); // grand écran : menu réduit au départ, en colonne d'icônes
  const [tiroirOuvert, setTiroirOuvert] = useState(false); // téléphone : le menu en tiroir
  const fermerTiroir = useCallback(() => setTiroirOuvert(false), []);

  // Sur téléphone, Wakil et le menu s'ouvrent par-dessus la page : le reste devient inerte
  // (ni clic, ni touche Tab, ni lecteur d'écran), comme derrière toute fenêtre modale.
  const inerte = !ecranLarge && (wakilOuvert || tiroirOuvert);

  if (erreur) {
    return (
      <p role="alert" className="m-4 rounded-2xl border border-bordure bg-surface p-6 text-attenue lg:m-10">
        {erreur}
      </p>
    );
  }
  // data-coquille fixe la hauteur de la page à celle de l'écran (globals.css) : seul <main> défile.
  // Téléphone : en-tête / contenu / barre du bas, en colonne. Grand écran : menu / contenu / Wakil, en ligne.
  // {children} est toujours rendu (chaque page attend le compte elle-même) : Next peut ainsi valider les pages.
  // La conversation est remise à neuf quand le client change (key) : rien ne passe d'un client à l'autre.
  return (
    <FournisseurConversation key={espace?.profil.id ?? "sans-client"}>
      <div data-coquille className="flex min-h-0 flex-1 flex-col lg:flex-row">
        {espace && <EnTeteMobile espace={espace} ouvrirMenu={() => setTiroirOuvert(true)} inerte={inerte} />}
        {espace && <Menu espace={espace} ouvert={menuOuvert} basculer={() => setMenuOuvert(!menuOuvert)} />}
        {/* Grand écran, Wakil fermé : plus de marge en bas, pour que le bouton flottant ne cache pas la fin du contenu */}
        <main
          inert={inerte}
          className={`flex min-h-0 min-w-0 flex-1 flex-col gap-5 overflow-y-auto px-4 pt-1 pb-10 lg:gap-6 lg:px-8.5 lg:pt-7 ${wakilOuvert ? "lg:pb-12" : "lg:pb-28"}`}
        >
          {!espace && <p className="text-attenue">Chargement de votre espace…</p>}
          {children}
        </main>
        {espace && <BarreBas espace={espace} inerte={inerte} />}
        {espace && <MenuMobile espace={espace} ouvert={tiroirOuvert} fermer={fermerTiroir} />}
        {espace && <PanneauWakil />}
      </div>
    </FournisseurConversation>
  );
}
