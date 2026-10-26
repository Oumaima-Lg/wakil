const nombre = new Intl.NumberFormat("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Montant à la marocaine : « 2 350 DH », « -57,98 DH ». Le montant arrive de l'API en texte exact (« 2350.00 »). */
export function dh(montant: string | number): string {
  const texte = nombre.format(Number(montant));
  return `${texte.endsWith(",00") ? texte.slice(0, -3) : texte} DH`;
}

/** Initiales pour les pastilles : « Salma Alaoui » → « SA ». */
export function initiales(prenom: string, nom: string): string {
  return `${prenom[0] ?? ""}${nom[0] ?? ""}`.toUpperCase();
}

/** Même chose pour un nom complet : « Fatima Lahlou » → « FL ». */
export function initialesNom(nomComplet: string): string {
  const [prenom = "", ...reste] = nomComplet.split(" ");
  return initiales(prenom, reste.join(" "));
}

/** Pour l'affichage d'un texte de Wakil : « 2 101 DH » ne doit jamais se couper en fin de ligne (espaces insécables). */
export function insecables(texte: string): string {
  return texte.replace(/(\d) (?=\d{3}\b)/g, "$1 ").replace(/ DH\b/g, " DH");
}
