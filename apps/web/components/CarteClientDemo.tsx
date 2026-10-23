"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { dh, initiales } from "@/lib/format";

/** Un client de démo tel que renvoyé par GET /clients-demo (agent-api), avec le résumé de son compte. */
export type ClientDemo = {
  id: number;
  civilite: "madame" | "monsieur";
  prenom: string;
  nom: string;
  ville: string;
  scenario: string;
  solde: string;
  plafond_virement: string;
  factures_a_payer: number;
  total_a_payer: string;
};

/** Composant client : il réagit au clic (« use client »). Le reste de l'accueil est rendu sur le serveur. */
export function CarteClientDemo({ client }: { client: ClientDemo }) {
  const router = useRouter();
  const [etat, setEtat] = useState<"repos" | "connexion" | "erreur">("repos");

  async function ouvrirEspace() {
    setEtat("connexion");
    try {
      // Passe par le proxy /api → agent-api, qui répond avec le cookie de session (jeton signé, HttpOnly).
      const reponse = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: client.id }),
      });
      if (!reponse.ok) throw new Error(String(reponse.status));
      router.push("/banque");
    } catch {
      setEtat("erreur");
    }
  }

  return (
    <article className="flex min-w-0 flex-[1_1_300px] flex-col gap-5 rounded-3xl border border-bordure bg-surface p-7">
      <div className="flex items-center gap-3.5">
        <span
          aria-hidden="true"
          className="flex size-13 flex-none items-center justify-center rounded-full border-[1.5px] border-accent text-[17px] font-semibold tracking-wide text-accent"
        >
          {initiales(client.prenom, client.nom)}
        </span>
        <div className="flex flex-col gap-0.5">
          <h3 className="text-[19px] font-semibold">
            {client.prenom} {client.nom}
          </h3>
          <p className="text-sm text-attenue">{client.ville}</p>
        </div>
      </div>

      <span className="self-start rounded-full border border-note-bordure bg-surligne px-3 py-1 text-[13px] font-medium text-note-texte">
        {client.scenario}
      </span>

      <dl className="flex flex-col gap-2.5 text-[15px]">
        <div className="flex justify-between gap-3">
          <dt className="text-attenue">Solde</dt>
          <dd className="font-semibold">{dh(client.solde)}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-attenue">Factures à payer</dt>
          <dd className="font-semibold">
            {client.factures_a_payer} · {dh(client.total_a_payer)}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-attenue">Plafond de virement</dt>
          <dd className="font-semibold">{dh(client.plafond_virement)}</dd>
        </div>
      </dl>

      <button
        type="button"
        onClick={ouvrirEspace}
        disabled={etat === "connexion"}
        className="mt-auto min-h-[50px] cursor-pointer rounded-full border-[1.5px] border-accent font-semibold tracking-wide transition-colors hover:bg-accent hover:text-sur-accent disabled:cursor-wait disabled:opacity-60"
      >
        {etat === "connexion" ? "Ouverture…" : `Ouvrir l'espace de ${client.prenom} →`}
      </button>
      {etat === "erreur" && (
        <p role="alert" className="text-sm text-alerte">
          La connexion a échoué. Réessayez dans un instant.
        </p>
      )}
    </article>
  );
}
