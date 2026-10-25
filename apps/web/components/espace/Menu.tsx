"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { CarteBancaire, Deplier, Etoile, Grille, Liste, Montagnes, Personnes, Recu, Replier } from "@/components/icones";
import { initiales } from "@/lib/format";
import type { Espace } from "@/lib/types";

const ENTREES = [
  { href: "/banque", libelle: "Vue d'ensemble", Icone: Grille },
  { href: "/banque/operations", libelle: "Opérations", Icone: Liste },
  { href: "/banque/factures", libelle: "Factures", Icone: Recu },
  { href: "/banque/beneficiaires", libelle: "Bénéficiaires", Icone: Personnes },
  { href: "/banque/carte", libelle: "Ma carte", Icone: CarteBancaire },
];

type Props = { espace: Espace; ouvert: boolean; basculer: () => void };

/** Le menu de gauche : ouvert (icônes + libellés) ou replié en colonne d'icônes. */
export function Menu({ espace, ouvert, basculer }: Props) {
  const chemin = usePathname(); // la page affichée, pour mettre son entrée en surbrillance
  const router = useRouter();
  const aPayer = espace.factures.filter((f) => f.statut === "impayee").length;
  const { prenom, nom } = espace.profil;

  async function seDeconnecter() {
    await fetch("/api/session", { method: "DELETE" });
    router.replace("/");
  }

  return (
    <nav
      aria-label="Menu de la banque"
      className={`flex flex-none flex-col gap-7 overflow-y-auto border-r border-[#2e3034] bg-menu py-6 ${ouvert ? "w-62 px-4" : "w-19 items-center"}`}
    >
      <div className={`flex items-center gap-2 ${ouvert ? "justify-between" : "flex-col"}`}>
        <Link href="/" className="flex items-center gap-2.5 px-1.5 text-accent" aria-label="Banque Atlas Démo, accueil">
          <Montagnes taille={30} />
          {ouvert && (
            <span className="flex flex-col leading-tight">
              <span className="text-[17px] font-semibold tracking-wide text-texte">Banque Atlas</span>
              <span className="text-[11px] font-medium tracking-[0.22em] uppercase">Démo</span>
            </span>
          )}
        </Link>
        <button
          type="button"
          onClick={basculer}
          aria-label={ouvert ? "Réduire le menu" : "Ouvrir le menu"}
          className="flex size-11 flex-none cursor-pointer items-center justify-center rounded-xl border border-bordure text-texte-2 hover:border-accent"
        >
          {ouvert ? <Replier taille={18} /> : <Deplier taille={18} />}
        </button>
      </div>

      <ul className="flex flex-col gap-1">
        {ENTREES.map(({ href, libelle, Icone }) => {
          const actif = chemin === href;
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={actif ? "page" : undefined}
                aria-label={ouvert ? undefined : libelle}
                className={`flex min-h-11 items-center gap-3 rounded-xl text-[15px] ${ouvert ? "px-3" : "size-11.5 justify-center"} ${actif ? "bg-surligne text-accent" : "text-texte-2 hover:text-texte"}`}
              >
                <Icone taille={19} />
                {ouvert && libelle}
                {ouvert && href === "/banque/factures" && aPayer > 0 && (
                  <span className="ml-auto min-w-[22px] rounded-full bg-bordure-forte px-1.5 text-center text-xs font-semibold text-texte">
                    {aPayer}
                  </span>
                )}
              </Link>
            </li>
          );
        })}
      </ul>

      <div className="mt-auto flex flex-col gap-3.5">
        {ouvert && (
          <div className="flex flex-col gap-2.5 rounded-[18px] border border-note-bordure bg-note p-4">
            <p className="flex items-center gap-2 text-sm font-semibold">
              <Etoile taille={18} className="text-accent" />
              Wakil, votre assistant
            </p>
            <p className="text-[13px] leading-normal text-attenue">Posez vos questions et faites vos opérations en darija.</p>
          </div>
        )}
        <div className={`flex items-center gap-2.5 ${ouvert ? "px-1.5" : "flex-col"}`}>
          <span
            aria-hidden="true"
            className="flex size-9 flex-none items-center justify-center rounded-full border-[1.5px] border-accent text-xs font-semibold text-accent"
          >
            {initiales(prenom, nom)}
          </span>
          {ouvert ? (
            <div className="flex min-w-0 flex-col">
              <span className="text-sm font-semibold">
                {prenom} {nom}
              </span>
              <button type="button" onClick={seDeconnecter} className="cursor-pointer self-start text-[13px] text-attenue underline">
                Se déconnecter
              </button>
            </div>
          ) : (
            <button type="button" onClick={seDeconnecter} className="cursor-pointer text-[11px] text-attenue underline">
              Sortir
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
