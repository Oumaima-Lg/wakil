"use client";

import { useState } from "react";

import { useEspace } from "@/components/espace/ContexteEspace";
import { Bloc, EnTetePage, LigneOperation, Tuile } from "@/components/espace/elements";
import { Recherche } from "@/components/icones";
import { duMois, groupesParMois, nomDuMois, resumeDuMois } from "@/lib/espace";
import { dh } from "@/lib/format";

const FILTRES = { tout: "Tout", depenses: "Dépenses", entrees: "Entrées" } as const;
type Filtre = keyof typeof FILTRES;

/** « Vêtements » et « vetements » se valent : on compare sans accents ni majuscules. */
const simplifier = (texte: string) =>
  texte
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();

/** Toutes les opérations du compte, regroupées par mois, avec un filtre et une recherche. */
export default function Operations() {
  const { espace } = useEspace();
  const [filtre, setFiltre] = useState<Filtre>("tout");
  const [recherche, setRecherche] = useState("");
  if (!espace) return null; // en attendant, la coquille affiche « Chargement… »
  const { compte, operations } = espace;
  const resume = resumeDuMois(operations);

  // Le filtrage se fait dans le navigateur : les 50 dernières opérations sont déjà chargées.
  const cherche = simplifier(recherche.trim());
  const visibles = operations.filter((o) => {
    const montant = Number(o.montant);
    if (filtre === "depenses" && montant >= 0) return false;
    if (filtre === "entrees" && montant <= 0) return false;
    return simplifier(o.libelle).includes(cherche);
  });

  return (
    <>
      <EnTetePage surtitre={`Compte courant ${compte.rib_masque}`} titre="Opérations" />

      <div className="flex flex-wrap gap-5.5">
        <Tuile libelle={`Dépenses ${duMois()}`} valeur={dh(resume.depenses)} />
        <Tuile libelle={`Entrées ${duMois()}`} valeur={dh(resume.entrees)} />
        <Tuile libelle={`Opérations en ${nomDuMois()}`} valeur={String(resume.nombre)} />
      </div>

      <Bloc aria-label="Toutes les opérations" className="flex flex-col gap-4.5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div role="group" aria-label="Filtrer les opérations" className="flex gap-2">
            {(Object.keys(FILTRES) as Filtre[]).map((cle) => (
              <button
                key={cle}
                type="button"
                aria-pressed={filtre === cle}
                onClick={() => setFiltre(cle)}
                className={`min-h-10 cursor-pointer rounded-full border px-4 text-sm ${filtre === cle ? "border-accent bg-surligne font-medium text-accent" : "border-bordure-forte text-texte-2"}`}
              >
                {FILTRES[cle]}
              </button>
            ))}
          </div>
          <div className="flex min-h-10.5 items-center gap-2 rounded-full border border-bordure-forte bg-[#202125] px-3.5">
            <Recherche taille={16} className="text-attenue" />
            <label htmlFor="recherche-op" className="sr-only">
              Rechercher une opération
            </label>
            <input
              id="recherche-op"
              type="search"
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
              placeholder="Rechercher une opération"
              className="w-55 bg-transparent text-sm placeholder:text-faible focus:outline-none"
            />
          </div>
        </div>

        {visibles.length === 0 ? (
          <p className="py-4 text-sm text-attenue">Aucune opération ne correspond.</p>
        ) : (
          groupesParMois(visibles).map((g) => (
            <div key={g.mois} className="flex flex-col">
              <div className="flex justify-between gap-3 py-2.5 text-[13px] font-medium tracking-[0.06em] text-attenue uppercase">
                <span>{g.mois}</span>
                <span className="tabular-nums">{dh(g.total)}</span>
              </div>
              <ul>
                {g.lignes.map((o) => (
                  <LigneOperation key={o.id} operation={o} complete />
                ))}
              </ul>
            </div>
          ))
        )}
        <p className="text-[13px] text-faible">
          Astuce : demandez à Wakil « 3tini la liste dyal les transactions dyali ».
        </p>
      </Bloc>
    </>
  );
}
