import { Info } from "./icones";

/** Mention obligatoire (règle n° 3 du projet), affichée en haut de toutes les pages. */
export function BandeauFictif() {
  return (
    <div role="note" className="border-b border-note-bordure bg-note px-4 py-1.5 sm:py-2">
      <p className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-2.5 gap-y-1 text-center text-xs text-note-texte sm:text-sm">
        <Info taille={16} className="hidden sm:block" />
        <strong className="font-semibold">Données 100 % fictives – projet de démonstration.</strong>
        {/* Sur téléphone, la première phrase suffit : la mention obligatoire reste visible sans prendre trois lignes */}
        <span className="hidden sm:inline">« Banque Atlas Démo » n&apos;existe pas : aucun client, compte ou fournisseur n&apos;est réel.</span>
      </p>
    </div>
  );
}
