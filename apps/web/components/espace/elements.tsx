"use client";

import Link from "next/link";

import { Etoile, Info } from "@/components/icones";
import { dateComplete, jour } from "@/lib/espace";
import { dh } from "@/lib/format";
import type { Facture, Operation } from "@/lib/types";

import { useEspace } from "./ContexteEspace";

/** En-tête de chaque page de l'espace, avec « Demander à Wakil » quand son panneau est fermé. */
export function EnTetePage({ surtitre, titre }: { surtitre: string; titre: string }) {
  const { wakilOuvert, setWakilOuvert } = useEspace();
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex flex-col gap-1">
        <p className="text-sm text-attenue">{surtitre}</p>
        <h1 className="text-3xl font-semibold">{titre}</h1>
      </div>
      {!wakilOuvert && (
        <button
          type="button"
          onClick={() => setWakilOuvert(true)}
          className="inline-flex min-h-11.5 cursor-pointer items-center gap-2.5 rounded-full border-[1.5px] border-accent px-5 font-semibold"
        >
          <Etoile taille={18} className="text-accent" />
          Demander à Wakil
        </button>
      )}
    </div>
  );
}

/** Un bloc de contenu (fond gris un peu plus clair, coins arrondis). */
export function Bloc({ className = "", ...props }: React.HTMLAttributes<HTMLElement>) {
  return <section className={`min-w-0 rounded-3xl border border-bordure bg-surface px-6 py-5.5 ${className}`} {...props} />;
}

/** Titre d'un bloc, avec un lien « Tout voir » vers la page détaillée. */
export function TitreBloc({ id, titre, lien }: { id: string; titre: string; lien?: string }) {
  return (
    <div className="flex items-center justify-between gap-3 pb-2">
      <h2 id={id} className="text-lg font-semibold">
        {titre}
      </h2>
      {lien && (
        <Link href={lien} className="text-sm text-accent underline-offset-4 hover:underline">
          Tout voir
        </Link>
      )}
    </div>
  );
}

/** Une petite tuile avec un chiffre : « Dépenses d'octobre · 6 374,08 DH ». */
export function Tuile({ libelle, valeur }: { libelle: string; valeur: string }) {
  return (
    <div className="flex-[1_1_200px] rounded-[20px] border border-bordure bg-surface px-5.5 py-5">
      <p className="text-[13px] text-attenue">{libelle}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{valeur}</p>
    </div>
  );
}

/** Une note d'information sur fond vert très sombre. */
export function Note({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`flex gap-3 rounded-[20px] border border-note-bordure bg-note px-5.5 py-5 ${className}`}>
      <Info taille={20} className="mt-0.5 flex-none text-accent" />
      <p className="text-sm leading-relaxed text-texte-2">{children}</p>
    </div>
  );
}

/** Montant signé : « +500 DH » pour une entrée, « -57,98 DH » pour une dépense. */
export const montantSigne = (montant: string) => `${Number(montant) > 0 ? "+" : ""}${dh(montant)}`;

/** Une ligne d'opération : date, libellé, montant. `complete` affiche l'année (page Opérations). */
export function LigneOperation({ operation, complete = false }: { operation: Operation; complete?: boolean }) {
  return (
    <li
      className={`-mx-2.5 grid items-center gap-3.5 rounded-xl border-t border-bordure px-2.5 py-3 ${complete ? "grid-cols-[110px_minmax(0,1fr)_auto]" : "grid-cols-[58px_minmax(0,1fr)_auto]"}`}
    >
      <span className="text-sm text-attenue tabular-nums">
        {complete ? dateComplete(operation.date) : jour(operation.date)}
      </span>
      <span className="min-w-0 text-[15px]">{operation.libelle}</span>
      <span className="text-right text-[15px] font-semibold tabular-nums">{montantSigne(operation.montant)}</span>
    </li>
  );
}

/** « À payer » ou « Payée ». */
export function StatutFacture({ facture }: { facture: Facture }) {
  return facture.statut === "impayee" ? (
    <span className="rounded-full border border-[#5a5d62] px-2.5 py-1 text-[12.5px] font-medium">À payer</span>
  ) : (
    <span className="rounded-full border border-bordure-forte bg-[#2a2c30] px-2.5 py-1 text-[12.5px] font-medium text-attenue">
      Payée
    </span>
  );
}
