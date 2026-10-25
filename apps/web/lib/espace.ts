import type { Operation } from "./types";

// Les dates de la banque sont en UTC ; on les affiche à l'heure du Maroc (le fuseau suit les décisions officielles).
const FUSEAU = "Africa/Casablanca";
const formatJour = new Intl.DateTimeFormat("fr-FR", { timeZone: FUSEAU, day: "2-digit", month: "2-digit" });
const formatDate = new Intl.DateTimeFormat("fr-FR", { timeZone: FUSEAU, day: "2-digit", month: "2-digit", year: "numeric" });
const formatMois = new Intl.DateTimeFormat("fr-FR", { timeZone: FUSEAU, month: "long", year: "numeric" });
const formatMoisSeul = new Intl.DateTimeFormat("fr-FR", { timeZone: FUSEAU, month: "long" });
const formatCle = new Intl.DateTimeFormat("fr-CA", { timeZone: FUSEAU, year: "numeric", month: "2-digit" });
const formatAujourdhui = new Intl.DateTimeFormat("fr-FR", {
  timeZone: FUSEAU,
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
});

const majuscule = (texte: string) => texte.charAt(0).toUpperCase() + texte.slice(1);

export const jour = (iso: string) => formatJour.format(new Date(iso)); // « 21/10 »
export const dateComplete = (iso: string) => formatDate.format(new Date(iso)); // « 21/10/2026 »
export const dateDuJour = () => majuscule(formatAujourdhui.format(new Date())); // « Vendredi 23 octobre 2026 »
const cleMois = (date: Date) => formatCle.format(date).slice(0, 7); // « 2026-10 », pour regrouper

export const nomDuMois = (date: Date = new Date()) => formatMoisSeul.format(date); // « octobre »

/** « d'octobre », « de septembre » : l'élision française devant une voyelle. */
export function duMois(date: Date = new Date()): string {
  const mois = nomDuMois(date);
  return /^[aeiouyéè]/i.test(mois) ? `d'${mois}` : `de ${mois}`;
}

// Les calculs se font en centimes entiers : jamais d'erreur d'arrondi comme 0,1 + 0,2 = 0,30000000000000004.
const centimes = (montant: string) => Math.round(Number(montant) * 100);

/** Somme exacte de montants reçus en texte (« 312.00 »). */
export const somme = (montants: string[]) => montants.reduce((total, m) => total + centimes(m), 0) / 100;

export type Categorie = { libelle: string; total: number };

/** Résumé du mois en cours : dépenses, entrées, nombre d'opérations et dépenses par catégorie. */
export function resumeDuMois(operations: Operation[], reference: Date = new Date()) {
  const cle = cleMois(reference);
  const duMoisCourant = operations.filter((o) => cleMois(new Date(o.date)) === cle);
  const parCategorie = new Map<string, number>();
  let depenses = 0;
  let entrees = 0;
  for (const o of duMoisCourant) {
    const c = centimes(o.montant);
    if (c < 0) {
      depenses -= c;
      parCategorie.set(o.libelle, (parCategorie.get(o.libelle) ?? 0) - c);
    } else {
      entrees += c;
    }
  }
  const categories: Categorie[] = [...parCategorie.entries()]
    .map(([libelle, total]) => ({ libelle, total: total / 100 }))
    .sort((a, b) => b.total - a.total);
  return {
    mois: majuscule(formatMois.format(reference)),
    depenses: depenses / 100,
    entrees: entrees / 100,
    nombre: duMoisCourant.length,
    categories,
  };
}

export type GroupeMois = { mois: string; total: number; lignes: Operation[] };

/** Opérations regroupées par mois, dans l'ordre reçu (de la plus récente à la plus ancienne). */
export function groupesParMois(operations: Operation[]): GroupeMois[] {
  const groupes = new Map<string, { mois: string; centimes: number; lignes: Operation[] }>();
  for (const o of operations) {
    const date = new Date(o.date);
    const cle = cleMois(date);
    if (!groupes.has(cle)) groupes.set(cle, { mois: majuscule(formatMois.format(date)), centimes: 0, lignes: [] });
    const groupe = groupes.get(cle)!;
    groupe.lignes.push(o);
    groupe.centimes += centimes(o.montant);
  }
  return [...groupes.values()].map((g) => ({ mois: g.mois, total: g.centimes / 100, lignes: g.lignes }));
}
