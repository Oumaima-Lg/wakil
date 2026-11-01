"use client";

import { useState } from "react";

import { Carte } from "@/components/Carte";
import { useEspace } from "@/components/espace/ContexteEspace";
import { EnTetePage, Note } from "@/components/espace/elements";
import { carteActuelle, ETATS_CARTE, grisee, libelleEtat } from "@/lib/cartes";
import type { CarteBancaire } from "@/lib/types";

const BOUTON =
  "min-h-11 cursor-pointer rounded-full px-4.5 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50";

type Action = "blocage" | "deblocage" | "opposition" | "remplacement";

/** Les actions sur la carte : bloquer ou débloquer, faire opposition, puis commander une nouvelle carte (Wakil, lui,
 *  peut seulement bloquer). Chacune demande une confirmation ; l'opposition, définitive, demande aussi son motif. La
 *  banque vérifie l'état de la carte. */
function ActionsCarte({ carte, apres }: { carte: CarteBancaire; apres: () => Promise<void> }) {
  const [ouverte, setOuverte] = useState<Action | null>(null);
  const [motif, setMotif] = useState<"perte" | "vol" | null>(null);
  const [occupe, setOccupe] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  // Définitif : après une opposition, il ne reste qu'à commander une nouvelle carte (une seule fois)
  if (carte.statut === "opposee" && carte.remplacee_par !== null) return null;

  async function confirmer(action: Action) {
    setOccupe(true);
    setErreur(null);
    const reponse = await fetch(`/api/moi/cartes/${carte.id}/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: action === "opposition" ? JSON.stringify({ motif }) : undefined,
    }).catch(() => null); // null : réseau coupé
    if (reponse?.ok) {
      setOuverte(null);
      await apres(); // l'espace se recharge : la page montre le nouvel état
    } else {
      const detail = reponse ? (await reponse.json().catch(() => null))?.detail : null;
      setErreur(detail?.message ?? "La banque ne répond pas. Réessayez dans un instant.");
    }
    setOccupe(false);
  }

  function annuler() {
    setOuverte(null);
    setMotif(null);
  }

  return (
    <section
      aria-label="Actions sur la carte"
      className="flex flex-col gap-3 rounded-[22px] border border-bordure bg-surface p-4.5 sm:p-6"
    >
      {ouverte === null && carte.statut === "opposee" && (
        <div className="flex flex-wrap gap-2.5">
          <button type="button" onClick={() => setOuverte("remplacement")} className={`${BOUTON} bg-accent text-sur-accent`}>
            Commander une nouvelle carte
          </button>
        </div>
      )}
      {ouverte === "remplacement" && (
        <>
          <p className="text-[15px] font-medium">
            Commander une nouvelle carte ? Elle aura un nouveau numéro ; {carte.numero_masque} reste en opposition.
          </p>
          <div className="flex flex-wrap gap-2.5">
            <button
              type="button"
              disabled={occupe}
              onClick={() => confirmer("remplacement")}
              className={`${BOUTON} bg-accent text-sur-accent`}
            >
              Oui, commander
            </button>
            <button type="button" disabled={occupe} onClick={annuler} className={`${BOUTON} border-[1.5px] border-[#5a5d62]`}>
              Annuler
            </button>
          </div>
        </>
      )}
      {ouverte === null && carte.statut !== "opposee" && (
        <div className="flex flex-wrap gap-2.5">
          {carte.statut === "active" && (
            <button
              type="button"
              onClick={() => setOuverte("blocage")}
              className={`${BOUTON} border-[1.5px] border-[#8a6a2e] text-[#f5cb80]`}
            >
              Bloquer la carte
            </button>
          )}
          {carte.statut === "bloquee" && (
            <button type="button" onClick={() => setOuverte("deblocage")} className={`${BOUTON} bg-accent text-sur-accent`}>
              Débloquer la carte
            </button>
          )}
          <button
            type="button"
            onClick={() => setOuverte("opposition")}
            className={`${BOUTON} border-[1.5px] border-[#8a3a2e] text-[#f5a080]`}
          >
            Faire opposition (perte ou vol)
          </button>
        </div>
      )}
      {ouverte === "blocage" && (
        <>
          <p className="text-[15px] font-medium">
            Bloquer la carte {carte.numero_masque} ? Vous pourrez la débloquer ici à tout moment ; tant qu&apos;elle est
            bloquée, Wakil reste en mode sécurité.
          </p>
          <div className="flex flex-wrap gap-2.5">
            <button
              type="button"
              disabled={occupe}
              onClick={() => confirmer("blocage")}
              className={`${BOUTON} bg-[#8a6a2e] text-white`}
            >
              Oui, bloquer
            </button>
            <button type="button" disabled={occupe} onClick={annuler} className={`${BOUTON} border-[1.5px] border-[#5a5d62]`}>
              Annuler
            </button>
          </div>
        </>
      )}
      {ouverte === "deblocage" && (
        <>
          <p className="text-[15px] font-medium">Débloquer la carte {carte.numero_masque} ?</p>
          <div className="flex flex-wrap gap-2.5">
            <button
              type="button"
              disabled={occupe}
              onClick={() => confirmer("deblocage")}
              className={`${BOUTON} bg-accent text-sur-accent`}
            >
              Oui, débloquer
            </button>
            <button type="button" disabled={occupe} onClick={annuler} className={`${BOUTON} border-[1.5px] border-[#5a5d62]`}>
              Annuler
            </button>
          </div>
        </>
      )}
      {ouverte === "opposition" && (
        <>
          <p className="text-[15px] font-medium">Pourquoi faire opposition sur la carte {carte.numero_masque} ?</p>
          <div role="radiogroup" aria-label="Motif de l'opposition" className="flex gap-2.5">
            {(["perte", "vol"] as const).map((choix) => (
              <button
                key={choix}
                type="button"
                role="radio"
                aria-checked={motif === choix}
                onClick={() => setMotif(choix)}
                className={`${BOUTON} border-[1.5px] ${motif === choix ? "border-accent text-accent" : "border-[#5a5d62]"}`}
              >
                {choix === "perte" ? "Perte" : "Vol"}
              </button>
            ))}
          </div>
          <p className="text-sm text-[#f5a080]">Définitif : la carte ne pourra plus jamais être utilisée.</p>
          <div className="flex flex-wrap gap-2.5">
            <button
              type="button"
              disabled={occupe || motif === null}
              onClick={() => confirmer("opposition")}
              className={`${BOUTON} bg-[#8a3a2e] text-white`}
            >
              Confirmer l&apos;opposition
            </button>
            <button type="button" disabled={occupe} onClick={annuler} className={`${BOUTON} border-[1.5px] border-[#5a5d62]`}>
              Annuler
            </button>
          </div>
        </>
      )}
      {erreur && (
        <p role="alert" className="text-sm text-[#f5cb80]">
          {erreur}
        </p>
      )}
    </section>
  );
}

/** La carte du client, avec son état réel dans la banque (après un blocage avec Wakil, elle passe à « Bloquée »). */
export default function MaCarte() {
  const { espace, recharger } = useEspace();
  if (!espace) return null; // en attendant, la coquille affiche « Chargement… »
  const { profil, compte, cartes } = espace;
  const carte = carteActuelle(cartes);
  const anciennes = cartes.filter((c) => c.id !== carte?.id); // les cartes remplacées, gardées pour l'historique
  const titulaire = `${profil.prenom} ${profil.nom}`;
  const rib = compte.rib_masque.replace(" ", " "); // espace insécable : « •••• 9114 » ne se coupe jamais en deux
  if (!carte) {
    return (
      <>
        <EnTetePage surtitre={`Compte courant ${compte.rib_masque}`} titre="Ma carte" />
        <Note>Aucune carte n&apos;est associée à ce compte.</Note>
      </>
    );
  }
  const fin = carte.numero_masque.slice(-4);

  const details = [
    ["Titulaire", titulaire],
    ["Numéro", `•••• •••• •••• ${fin}`],
    ["Expiration", carte.expiration],
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
        <Carte
          titulaire={titulaire}
          fin={fin}
          civilite={profil.civilite}
          expiration={carte.expiration}
          className={`w-[340px] max-w-full transition ${grisee(carte)}`}
        />
        <dl className="flex min-w-0 flex-[1_1_300px] flex-col text-[15px]">
          {details.map(([terme, valeur]) => (
            <div key={terme} className="flex justify-between gap-3 border-b border-[#36393e] py-2.75">
              <dt className="text-attenue">{terme}</dt>
              <dd className="text-right font-medium tabular-nums">{valeur}</dd>
            </div>
          ))}
          {anciennes.map((ancienne) => (
            <div key={ancienne.id} className="flex justify-between gap-3 border-b border-[#36393e] py-2.75">
              <dt className="text-attenue">Ancienne carte</dt>
              <dd className="text-right font-medium tabular-nums">
                {ancienne.numero_masque} · {libelleEtat(ancienne)}
              </dd>
            </div>
          ))}
          <div className="flex items-center justify-between gap-3 py-2.75">
            <dt className="text-attenue">Statut</dt>
            <dd>
              <span className={`rounded-full border px-3 py-1 text-[13px] font-medium ${ETATS_CARTE[carte.statut].pastille}`}>
                {libelleEtat(carte)}
              </span>
            </dd>
          </div>
        </dl>
      </section>

      <ActionsCarte carte={carte} apres={() => recharger(true)} />

      <Note>
        La carte est fictive. Vous pouvez la bloquer ici ou avec Wakil (« bloqui liya la carte »), toujours après votre
        confirmation. Le déblocage et l&apos;opposition se font ici seulement : Wakil ne peut pas réactiver une carte, et
        tant qu&apos;elle est bloquée ou en opposition, il reste en mode sécurité.
      </Note>
    </>
  );
}
