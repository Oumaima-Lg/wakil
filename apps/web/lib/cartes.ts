import type { CarteBancaire } from "@/lib/types";

/** L'état d'une carte, lu dans la banque : son libellé et sa pastille (pages Vue d'ensemble et Ma carte). */
export const ETATS_CARTE: Record<CarteBancaire["statut"], { libelle: string; pastille: string }> = {
  active: { libelle: "Active", pastille: "border-[#4a4e35] bg-surligne text-note-texte" },
  bloquee: { libelle: "Bloquée", pastille: "border-[#8a6a2e] bg-[#2b2720] text-[#f5cb80]" },
  opposee: { libelle: "En opposition", pastille: "border-[#8a3a2e] bg-[#2b2120] text-[#f5a080]" },
};

/** La carte à montrer : celle qui sert encore (active ou bloquée) ; sinon la plus récente, en opposition. */
export function carteActuelle(cartes: CarteBancaire[]): CarteBancaire | undefined {
  return cartes.find((c) => c.statut !== "opposee") ?? cartes.at(-1);
}

/** « Bloquée », « En opposition (vol) »… */
export function libelleEtat(carte: CarteBancaire): string {
  const { libelle } = ETATS_CARTE[carte.statut];
  return carte.motif_opposition ? `${libelle} (${carte.motif_opposition})` : libelle;
}

/** Une carte qui ne sert plus (bloquée, en opposition) est grisée. */
export const grisee = (carte: CarteBancaire | undefined) => (carte && carte.statut !== "active" ? "opacity-55 grayscale" : "");
