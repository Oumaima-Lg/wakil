import { Info } from "./icones";

/** Mention obligatoire (règle n° 3 du projet), affichée en haut de toutes les pages. */
export function BandeauFictif() {
  return (
    <div role="note" className="border-b border-note-bordure bg-note px-4 py-2">
      <p className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-2.5 gap-y-1 text-center text-sm text-note-texte">
        <Info taille={16} />
        <strong className="font-semibold">Données 100 % fictives – projet de démonstration.</strong>
        <span>« Banque Atlas Démo » n&apos;existe pas : aucun client, compte ou fournisseur n&apos;est réel.</span>
      </p>
    </div>
  );
}
