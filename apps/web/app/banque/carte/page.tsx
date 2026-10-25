"use client";

import { Carte } from "@/components/Carte";
import { useEspace } from "@/components/espace/ContexteEspace";
import { EnTetePage, Note } from "@/components/espace/elements";

const EXPIRATION = "10/29";

/** La carte de démo et ses détails. Aucun réglage n'est simulé : la page le dit clairement. */
export default function MaCarte() {
  const { espace } = useEspace();
  if (!espace) return null; // en attendant, la coquille affiche « Chargement… »
  const { profil, compte } = espace;
  const titulaire = `${profil.prenom} ${profil.nom}`;
  const fin = compte.rib_masque.slice(-4);
  const rib = compte.rib_masque.replace(" ", "\u00a0"); // espace insécable : « •••• 9114 » ne se coupe jamais en deux

  const details = [
    ["Titulaire", titulaire],
    ["Numéro", `•••• •••• •••• ${fin}`],
    ["Expiration", EXPIRATION],
    ["Type", "Carte de débit (démo)"],
    ["Compte associé", `Compte courant ${rib}`],
  ];

  return (
    <>
      <EnTetePage surtitre={`Compte courant ${compte.rib_masque}`} titre="Ma carte" />

      <section
        aria-label="Ma carte bancaire"
        className="flex flex-wrap items-start justify-center gap-6 rounded-[22px] border border-bordure bg-surface p-4.5 sm:justify-start sm:gap-8 sm:rounded-3xl sm:p-6.5"
      >
        <Carte titulaire={titulaire} fin={fin} civilite={profil.civilite} expiration={EXPIRATION} />
        <dl className="flex min-w-0 flex-[1_1_300px] flex-col text-[15px]">
          {details.map(([terme, valeur]) => (
            <div key={terme} className="flex justify-between gap-3 border-b border-[#36393e] py-2.75">
              <dt className="text-attenue">{terme}</dt>
              <dd className="text-right font-medium tabular-nums">{valeur}</dd>
            </div>
          ))}
          <div className="flex items-center justify-between gap-3 py-2.75">
            <dt className="text-attenue">Statut</dt>
            <dd>
              <span className="rounded-full border border-[#4a4e35] bg-surligne px-3 py-1 text-[13px] font-medium text-note-texte">
                Active
              </span>
            </dd>
          </div>
        </dl>
      </section>

      <Note>
        La carte est une illustration : les réglages d&apos;une vraie carte (blocage, paiement en ligne, sans contact)
        ne sont pas simulés dans cette démo.
      </Note>
    </>
  );
}
