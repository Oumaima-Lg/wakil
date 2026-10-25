"use client";

import { Carte } from "@/components/Carte";
import { useEspace } from "@/components/espace/ContexteEspace";
import { Bloc, EnTetePage, LigneOperation, StatutFacture, TitreBloc } from "@/components/espace/elements";
import { dateDuJour, duMois, resumeDuMois, somme } from "@/lib/espace";
import { dh, initialesNom } from "@/lib/format";

/** Vue d'ensemble : carte et solde, factures à payer, dernières opérations, bénéficiaires, dépenses du mois. */
export default function VueEnsemble() {
  const { espace, setWakilOuvert } = useEspace();
  if (!espace) return null; // en attendant, la coquille affiche « Chargement… »
  const { profil, compte, operations, factures, beneficiaires } = espace;
  const impayees = factures.filter((f) => f.statut === "impayee");
  // Les factures à payer d'abord, puis les dernières payées
  const apercuFactures = [...impayees, ...factures.filter((f) => f.statut === "payee").reverse()].slice(0, 4);
  const resume = resumeDuMois(operations);
  const plusGrande = resume.categories[0]?.total ?? 0;

  return (
    <>
      <EnTetePage surtitre={dateDuJour()} titre={`Bonjour ${profil.prenom}`} />

      <div className="flex flex-wrap gap-5.5">
        {/* @container : la mise en page suit la largeur de ce bloc (pas celle de l'écran), qui change quand on
            ouvre ou ferme le menu et Wakil. Il faut 568 px pour la carte (340) et le solde (200) côte à côte. */}
        <section
          aria-label="Compte courant"
          className="@container min-w-0 flex-[2_1_560px] rounded-3xl border-[1.5px] border-bordure bg-surface p-6"
        >
          <div className="flex flex-wrap items-center justify-center gap-7">
            {/* Entre 500 et 568 px : la carte passe à 80 % pour rester à côté du solde. En dessous : tout s'empile, centré. */}
            <div className="@min-[31.25rem]:@max-[35.5rem]:[zoom:0.8]">
              <Carte
                titulaire={`${profil.prenom} ${profil.nom}`}
                fin={compte.rib_masque.slice(-4)}
                civilite={profil.civilite}
              />
            </div>
            <div className="flex min-w-0 flex-[1_1_200px] flex-col gap-4.5 @max-[31.25rem]:text-center">
              <div className="flex flex-col gap-1">
                <p className="text-[13px] font-medium tracking-[0.08em] text-attenue uppercase">
                  Compte courant · solde disponible
                </p>
                <p className="text-[40px] font-semibold tracking-[0.01em] text-accent tabular-nums">
                  {dh(compte.solde)}
                </p>
              </div>
              <div className="flex flex-wrap gap-x-8 gap-y-3 border-t border-[#36393e] pt-3.5 @max-[31.25rem]:justify-center">
                <div className="flex flex-col gap-0.5">
                  <span className="text-[13px] text-attenue">Plafond de virement</span>
                  <span className="font-semibold tabular-nums">{dh(compte.plafond_virement)}</span>
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-[13px] text-attenue">Dépenses {duMois()}</span>
                  <span className="font-semibold tabular-nums">{dh(resume.depenses)}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          aria-labelledby="titre-a-payer"
          className="flex min-w-0 flex-[1_1_240px] flex-col gap-3 rounded-3xl border border-bordure bg-surface p-6"
        >
          <h2 id="titre-a-payer" className="text-[13px] font-medium tracking-[0.08em] text-attenue uppercase">
            À payer
          </h2>
          <p className="text-[32px] font-semibold tabular-nums">{dh(somme(impayees.map((f) => f.montant)))}</p>
          <p className="text-sm text-attenue">
            {impayees.length === 0
              ? "Aucune facture en attente"
              : `${impayees.length} facture${impayees.length > 1 ? "s" : ""} en attente`}
          </p>
          {impayees.length > 0 && (
            <button
              type="button"
              onClick={() => setWakilOuvert(true)}
              className="mt-auto min-h-11.5 cursor-pointer rounded-full border-[1.5px] border-accent text-sm font-semibold"
            >
              Payer avec Wakil
            </button>
          )}
        </section>
      </div>

      <div className="flex flex-wrap gap-5.5">
        <Bloc aria-labelledby="titre-operations" className="flex-[3_1_400px]">
          <TitreBloc id="titre-operations" titre="Dernières opérations" lien="/banque/operations" />
          <ul>
            {operations.slice(0, 6).map((o) => (
              <LigneOperation key={o.id} operation={o} />
            ))}
          </ul>
        </Bloc>

        <div className="flex min-w-0 flex-[2_1_300px] flex-col gap-5.5">
          <Bloc aria-labelledby="titre-factures">
            <TitreBloc id="titre-factures" titre="Factures" lien="/banque/factures" />
            <ul>
              {apercuFactures.map((f) => (
                <li
                  key={f.id}
                  className="-mx-2.5 flex flex-wrap items-center justify-between gap-x-3 gap-y-2 rounded-xl border-t border-bordure px-2.5 py-3"
                >
                  <div className="flex min-w-0 flex-col gap-0.5">
                    <span className="text-[15px]">{f.fournisseur}</span>
                    <span className="text-sm font-semibold tabular-nums">{dh(f.montant)}</span>
                  </div>
                  <StatutFacture facture={f} />
                </li>
              ))}
            </ul>
          </Bloc>

          <Bloc aria-labelledby="titre-beneficiaires">
            <TitreBloc id="titre-beneficiaires" titre="Bénéficiaires" lien="/banque/beneficiaires" />
            {beneficiaires.length === 0 ? (
              <p className="border-t border-bordure pt-3 text-sm text-attenue">Aucun bénéficiaire enregistré.</p>
            ) : (
              <ul>
                {beneficiaires.slice(0, 3).map((b) => (
                  <li key={b.id} className="flex items-center justify-between gap-3 border-t border-bordure py-3">
                    <div className="flex min-w-0 items-center gap-3">
                      <span
                        aria-hidden="true"
                        className="flex size-9.5 flex-none items-center justify-center rounded-full bg-bordure text-[13px] font-semibold"
                      >
                        {initialesNom(b.nom)}
                      </span>
                      <div className="flex min-w-0 flex-col">
                        <span className="text-[15px]">{b.nom}</span>
                        <span className="text-[13px] text-attenue tabular-nums">{b.rib_masque}</span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setWakilOuvert(true)}
                      className="cursor-pointer text-sm text-accent underline-offset-4 hover:underline"
                    >
                      Virer avec Wakil
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </Bloc>
        </div>
      </div>

      <Bloc aria-labelledby="titre-categories">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1.5 pb-3.5">
          <h2 id="titre-categories" className="text-lg font-semibold">
            Dépenses par catégorie
          </h2>
          <p className="text-sm text-attenue">
            {resume.mois} · {dh(resume.depenses)}
          </p>
        </div>
        {resume.categories.length === 0 ? (
          <p className="text-sm text-attenue">Aucune dépense ce mois-ci.</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {resume.categories.map((c) => (
              <li
                key={c.libelle}
                className="grid grid-cols-[minmax(110px,220px)_minmax(0,1fr)_auto] items-center gap-4 text-[14.5px]"
              >
                <span>{c.libelle}</span>
                <span aria-hidden="true" className="h-2.5 overflow-hidden rounded-full bg-bordure">
                  <span
                    className="block h-full rounded-full bg-accent"
                    style={{ width: `${Math.max(2, Math.round((c.total / plusGrande) * 100))}%` }}
                  />
                </span>
                <span className="text-right font-semibold tabular-nums">{dh(c.total)}</span>
              </li>
            ))}
          </ul>
        )}
      </Bloc>
    </>
  );
}
