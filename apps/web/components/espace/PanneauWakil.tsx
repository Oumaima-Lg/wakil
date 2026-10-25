"use client";

import { Deplier, Etoile, Fleche } from "@/components/icones";

import { useEspace } from "./ContexteEspace";

/** Le panneau de Wakil, à droite. Partie 7b : la coquille seulement ; la conversation arrive en 7c. */
export function PanneauWakil() {
  const { wakilOuvert, setWakilOuvert } = useEspace();

  if (!wakilOuvert) {
    return (
      <button
        type="button"
        onClick={() => setWakilOuvert(true)}
        className="fixed right-7 bottom-7 z-10 inline-flex min-h-14 cursor-pointer items-center gap-2.5 rounded-full bg-accent pr-6 pl-5 font-semibold text-sur-accent shadow-[0_18px_50px_-12px_#000000aa]"
      >
        <Etoile taille={22} />
        Wakil
      </button>
    );
  }

  return (
    <aside aria-label="Wakil, assistant en darija" className="flex w-96 flex-none flex-col border-l border-[#2e3034] bg-[#202125]">
      <div className="flex items-center justify-between gap-3 border-b border-surface-2 py-4 pr-4 pl-5">
        <div className="flex items-center gap-2.5">
          <Etoile taille={26} className="text-accent" />
          <div className="flex flex-col">
            <span className="text-[17px] font-semibold tracking-wide text-accent">Wakil</span>
            <span className="text-[12.5px] text-attenue">Votre assistant en darija</span>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setWakilOuvert(false)}
          aria-label="Fermer Wakil"
          className="flex size-11 cursor-pointer items-center justify-center rounded-xl border border-bordure-forte text-texte-2 hover:border-accent"
        >
          <Deplier taille={18} />
        </button>
      </div>

      {/* Seule cette zone défilera quand la conversation s'allongera : la saisie reste en bas, toujours visible */}
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-3 overflow-y-auto p-6 text-center">
        <Etoile taille={44} className="text-accent" />
        <p className="text-lg font-semibold">Kifach n9der n3awnek ?</p>
        <p className="text-sm text-attenue">La conversation avec Wakil arrive à la prochaine étape (7c).</p>
      </div>

      <div className="border-t border-surface-2 px-4 pt-3 pb-4.5">
        <div className="flex items-center gap-2 rounded-3xl border border-bordure-forte bg-surface py-1.5 pr-1.5 pl-4 opacity-60">
          <span className="flex-1 text-[15px] text-faible">Ktab hna…</span>
          <span className="flex size-11 items-center justify-center rounded-full bg-accent text-sur-accent">
            <Fleche taille={18} />
          </span>
        </div>
        <p className="mt-2 px-1 text-xs text-faible">Les montants viennent toujours de la banque, jamais de l&apos;IA.</p>
      </div>
    </aside>
  );
}
