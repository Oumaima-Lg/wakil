"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { CarteBancaire, Etoile, Grille, Liste, Montagnes, Recu, TroisTraits } from "@/components/icones";
import { initiales } from "@/lib/format";
import type { Espace } from "@/lib/types";

import { useEspace } from "./ContexteEspace";
import { nombreAPayer } from "./Menu";

type Props = { espace: Espace; ouvrirMenu: () => void; inerte: boolean };

/** L'en-tête du téléphone : bouton ☰ (menu), logo, et pastille du profil (qui ouvre aussi le menu). */
export function EnTeteMobile({ espace, ouvrirMenu, inerte }: Props) {
  const { prenom, nom } = espace.profil;
  return (
    <header inert={inerte} className="flex flex-none items-center justify-between gap-3 px-4 py-3 lg:hidden">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={ouvrirMenu}
          aria-label="Ouvrir le menu"
          className="-ml-1.5 flex size-11 cursor-pointer items-center justify-center rounded-xl"
        >
          <TroisTraits taille={22} />
        </button>
        <Montagnes taille={26} className="text-accent" />
        <span className="flex flex-col leading-tight">
          <span className="text-[15px] font-semibold tracking-wide">Banque Atlas</span>
          <span className="text-[10px] font-medium tracking-[0.22em] text-accent uppercase">Démo</span>
        </span>
      </div>
      <button
        type="button"
        onClick={ouvrirMenu}
        aria-label={`Mon profil : ${prenom} ${nom}`}
        className="size-11 cursor-pointer rounded-full border-[1.5px] border-accent text-[13px] font-semibold text-accent"
      >
        {initiales(prenom, nom)}
      </button>
    </header>
  );
}

const ONGLETS = [
  { href: "/banque", libelle: "Accueil", Icone: Grille },
  { href: "/banque/operations", libelle: "Opérations", Icone: Liste },
  { href: "/banque/factures", libelle: "Factures", Icone: Recu },
  { href: "/banque/carte", libelle: "Carte", Icone: CarteBancaire },
];

/** La barre du bas du téléphone : quatre onglets et, au centre, le bouton rond de Wakil. */
export function BarreBas({ espace, inerte }: { espace: Espace; inerte: boolean }) {
  const chemin = usePathname();
  const { setWakilOuvert } = useEspace();
  const aPayer = nombreAPayer(espace);

  const onglet = ({ href, libelle, Icone }: (typeof ONGLETS)[number]) => {
    const actif = chemin === href;
    return (
      <Link
        key={href}
        href={href}
        aria-current={actif ? "page" : undefined}
        className={`relative flex min-h-12 w-16 flex-col items-center justify-center gap-0.75 text-[11px] ${actif ? "font-medium text-accent" : "text-attenue"}`}
      >
        <Icone taille={22} />
        {libelle}
        {href === "/banque/factures" && aPayer > 0 && (
          <span className="absolute top-0.5 right-3 min-w-4.5 rounded-full bg-accent px-1.25 text-center text-[10.5px] leading-4.5 font-bold text-sur-accent">
            {aPayer}
          </span>
        )}
      </Link>
    );
  };

  return (
    <nav
      inert={inerte}
      aria-label="Navigation principale"
      className="flex flex-none items-end justify-around border-t border-[#2e3034] bg-menu px-1.5 pt-2 pb-3.5 lg:hidden"
    >
      {ONGLETS.slice(0, 2).map(onglet)}
      <button
        type="button"
        onClick={() => setWakilOuvert(true)}
        aria-label="Ouvrir Wakil, votre assistant en darija"
        className="flex w-16 cursor-pointer flex-col items-center gap-0.75 text-[11px] font-semibold"
      >
        <span className="-mt-6.5 flex size-14.5 items-center justify-center rounded-full border-4 border-menu bg-accent text-sur-accent shadow-[0_10px_26px_-10px_#000000cc]">
          <Etoile taille={26} />
        </span>
        Wakil
      </button>
      {ONGLETS.slice(2).map(onglet)}
    </nav>
  );
}
