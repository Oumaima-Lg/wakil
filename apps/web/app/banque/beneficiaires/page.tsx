"use client";

import { useWakil } from "@/components/espace/ContexteConversation";
import { useEspace } from "@/components/espace/ContexteEspace";
import { Bloc, EnTetePage, Note, Tuile } from "@/components/espace/elements";
import { dh, initialesNom } from "@/lib/format";

/** Les bénéficiaires de virement. Minimisation des données : ni ville ni RIB complet. */
export default function Beneficiaires() {
  const { espace, setWakilOuvert } = useEspace();
  const { proposer } = useWakil();
  if (!espace) return null; // en attendant, la coquille affiche « Chargement… »
  const { compte, beneficiaires } = espace;
  const exemple = beneficiaires[0]?.nom.split(" ")[0] ?? "Fatima";

  return (
    <>
      <EnTetePage surtitre="Pour vos virements" titre="Bénéficiaires" />

      <Bloc aria-label="Liste des bénéficiaires">
        {beneficiaires.length === 0 ? (
          <p className="text-sm text-attenue">Aucun bénéficiaire enregistré.</p>
        ) : (
          <ul className="flex flex-col">
            {beneficiaires.map((b, i) => (
              <li
                key={b.id}
                className={`flex flex-wrap items-center justify-between gap-3.5 py-3 ${i > 0 ? "border-t border-bordure" : ""}`}
              >
                <div className="flex min-w-0 items-center gap-3.5">
                  <span
                    aria-hidden="true"
                    className="flex size-12 flex-none items-center justify-center rounded-full bg-bordure text-[15px] font-semibold"
                  >
                    {initialesNom(b.nom)}
                  </span>
                  <div className="flex min-w-0 flex-col gap-0.5">
                    <span className="font-semibold">{b.nom}</span>
                    <span className="text-[13.5px] text-attenue">
                      RIB <span className="tabular-nums">{b.rib_masque}</span> ·{" "}
                      {b.interne ? "Client·e de la Banque Atlas Démo" : "Compte dans une autre banque"}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    // Le montant ne se devine pas : le champ est prérempli, le curseur attend après « sifet »
                    setWakilOuvert(true);
                    proposer(`sifet  DH l ${b.nom}`, 6);
                  }}
                  className="min-h-11.5 cursor-pointer rounded-full border-[1.5px] border-accent px-5 text-sm font-semibold"
                >
                  Virer avec Wakil
                </button>
              </li>
            ))}
          </ul>
        )}
      </Bloc>

      <div className="flex flex-wrap gap-5.5">
        <Tuile libelle="Plafond par virement" valeur={dh(compte.plafond_virement)} />
        <Note className="flex-[2_1_380px]">
          Pour un virement, dites par exemple à Wakil « sifet 500 DH l {exemple} ». L&apos;ajout de nouveaux
          bénéficiaires n&apos;est pas proposé dans cette démo.
        </Note>
      </div>
    </>
  );
}
