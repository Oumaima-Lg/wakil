"use client";

import { useEspace } from "@/components/espace/ContexteEspace";
import { Bloc, EnTetePage, StatutFacture } from "@/components/espace/elements";
import { Cadenas, Goutte, Mobile, Recu, Wifi } from "@/components/icones";
import { somme } from "@/lib/espace";
import { dh } from "@/lib/format";

// Les seuls fournisseurs possibles (règle CHECK de la base) : tous fictifs.
const ICONES = { "Eau & Électricité (démo)": Goutte, "Internet (démo)": Wifi, "Mobile (démo)": Mobile } as const;
const iconeDe = (fournisseur: string) => ICONES[fournisseur as keyof typeof ICONES] ?? Recu;

/** Les factures : celles à payer en cartes, celles déjà payées en liste. */
export default function Factures() {
  const { espace, setWakilOuvert } = useEspace();
  if (!espace) return null; // en attendant, la coquille affiche « Chargement… »
  const { factures } = espace;
  const impayees = factures.filter((f) => f.statut === "impayee");
  const payees = factures.filter((f) => f.statut === "payee").reverse(); // la plus récente d'abord

  return (
    <>
      <EnTetePage surtitre="Eau, internet, mobile" titre="Factures" />

      <section aria-labelledby="titre-a-payer" className="flex flex-col gap-3.5">
        <h2 id="titre-a-payer" className="text-lg font-semibold">
          À payer · {dh(somme(impayees.map((f) => f.montant)))}
        </h2>
        {impayees.length === 0 ? (
          <p className="text-sm text-attenue">Toutes vos factures sont payées.</p>
        ) : (
          <div className="flex flex-wrap gap-5.5">
            {impayees.map((f) => {
              const Icone = iconeDe(f.fournisseur);
              return (
                <article
                  key={f.id}
                  className="flex min-w-0 flex-[0_1_340px] flex-col gap-4 rounded-[22px] border border-bordure bg-surface p-5.5"
                >
                  <div className="flex items-center gap-3">
                    <span
                      aria-hidden="true"
                      className="flex size-11 flex-none items-center justify-center rounded-[14px] bg-surligne text-accent"
                    >
                      <Icone taille={22} />
                    </span>
                    <div className="flex flex-col">
                      <h3 className="font-semibold">{f.fournisseur}</h3>
                      <span className="text-[13px] text-attenue">Facture n° {f.id}</span>
                    </div>
                  </div>
                  <p className="text-3xl font-semibold text-accent tabular-nums">{dh(f.montant)}</p>
                  <button
                    type="button"
                    onClick={() => setWakilOuvert(true)}
                    className="min-h-11.5 cursor-pointer rounded-full bg-accent text-sm font-semibold text-sur-accent"
                  >
                    Payer avec Wakil
                  </button>
                </article>
              );
            })}
          </div>
        )}
        <p className="flex items-center gap-2 text-[13.5px] text-attenue">
          <Cadenas taille={16} />
          Chaque paiement passe par Wakil et demande toujours votre confirmation.
        </p>
      </section>

      <Bloc aria-labelledby="titre-payees">
        <h2 id="titre-payees" className="mb-2 text-lg font-semibold">
          Payées
        </h2>
        {payees.length === 0 ? (
          <p className="text-sm text-attenue">Aucune facture payée pour l&apos;instant.</p>
        ) : (
          <ul>
            {payees.map((f) => (
              <li
                key={f.id}
                className="-mx-2.5 flex flex-wrap items-center justify-between gap-x-3 gap-y-2 rounded-xl border-t border-bordure px-2.5 py-3"
              >
                <div className="flex flex-col gap-0.5">
                  <span className="text-[15px]">{f.fournisseur}</span>
                  <span className="text-[13px] text-attenue">Facture n° {f.id}</span>
                </div>
                <div className="flex items-center gap-3.5">
                  <span className="text-[15px] font-semibold tabular-nums">{dh(f.montant)}</span>
                  <StatutFacture facture={f} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </Bloc>
    </>
  );
}
