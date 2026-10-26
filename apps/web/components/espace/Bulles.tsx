"use client";

import Link from "next/link";

import { Attention, Cadenas, Coche, Echange, Etoile, Recu } from "@/components/icones";
import { jour } from "@/lib/espace";
import { dh, insecables } from "@/lib/format";
import type { Facture, Operation } from "@/lib/types";

import { montantSigne } from "./elements";
import type { Avancement, Carte, MessageWakil, StatutCarte } from "./useConversation";

const BULLE = "max-w-[90%] rounded-[20px] px-3.75 py-2.5 text-[15px] leading-normal";

// Une suggestion par façon d'écrire la darija : lettres latines, lettres arabes, mélange avec le français.
const SUGGESTIONS = [
  { texte: "chhal bqa f compte dyali ?", arabe: false },
  { texte: "شنو هوما آخر العمليات اللي درت؟", arabe: true },
  { texte: "wach 3ndi chi factures ma khlsthomch ?", arabe: false },
];

/** L'écran d'accueil du chat, avant le premier message. */
export function AccueilChat({ prenom, envoyer }: { prenom: string; envoyer: (texte: string) => void }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3.5 py-4 text-center">
      <Etoile taille={44} className="text-accent" />
      <p className="text-2xl font-semibold text-accent">Salam {prenom} !</p>
      <p className="text-[17px]">Kifach n9der n3awnek lyoum ?</p>
      <p className="text-sm leading-relaxed text-attenue">
        Écrivez en darija, en lettres arabes ou latines, ou mélangée au français. Essayez :
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {SUGGESTIONS.map(({ texte, arabe }) => (
          <button
            key={texte}
            type="button"
            onClick={() => envoyer(texte)}
            lang={arabe ? "ar" : undefined}
            dir={arabe ? "rtl" : "auto"}
            className={`min-h-11 cursor-pointer rounded-full border border-[#4a4e35] bg-surligne px-4 hover:border-accent ${arabe ? "font-arabe text-[15px]" : "text-sm"}`}
          >
            {texte}
          </button>
        ))}
      </div>
      <p className="text-xs leading-relaxed text-faible">
        Wakil consulte le solde, les opérations et les factures, paie une facture et fait un virement : toujours après
        votre confirmation.
      </p>
    </div>
  );
}

/** Le message du client : bulle vert-citron, à droite. dir="auto" : l'arabe s'écrit de droite à gauche. */
export function BulleClient({ texte }: { texte: string }) {
  return (
    <li className="flex justify-end">
      <p dir="auto" className={`${BULLE} rounded-br-md bg-accent break-words whitespace-pre-wrap text-sur-accent`}>
        {texte}
      </p>
    </li>
  );
}

type ProprietesBulle = { message: MessageWakil; reessayer: () => void; repondre: (reponse: "Oui" | "Non") => void };

/** La réponse de Wakil : texte simple, affichage riche selon l'outil (solde en grand, opérations en tableau), ou carte. */
export function BulleWakil({ message, reessayer, repondre }: ProprietesBulle) {
  if (message.carte) {
    return (
      <li className="flex flex-col gap-2">
        <p dir="auto" className={`${BULLE} self-start rounded-bl-md bg-surface-2`}>
          {message.carte.intro}
        </p>
        <CarteConfirmation carte={message.carte} repondre={repondre} />
      </li>
    );
  }
  if (message.erreur) {
    return (
      <li role="alert" className="flex">
        <div className={`${BULLE} flex flex-col gap-3 rounded-bl-md border border-[#8a6a2e] bg-[#2b2720]`}>
          <p dir="auto" className="flex gap-2">
            <Attention taille={18} className="mt-0.75 flex-none text-alerte" />
            {message.texte}
          </p>
          {message.demande && (
            <button
              type="button"
              onClick={reessayer}
              className="min-h-11 cursor-pointer self-start rounded-full border border-alerte px-4.5 text-sm font-medium"
            >
              Réessayer
            </button>
          )}
        </div>
      </li>
    );
  }
  // Après une confirmation : coche si l'opération est faite, encadré orange si la banque l'a refusée au dernier moment
  const faite = message.issue === "faite";
  const refusee = message.issue === "refusee";
  return (
    <li className="flex">
      <div className={`${BULLE} rounded-bl-md ${refusee ? "border border-[#8a6a2e] bg-[#2b2720]" : "bg-surface-2"}`}>
        {faite || refusee ? (
          <p dir="auto" className="flex gap-2">
            {faite ? (
              <Coche taille={18} className="mt-0.75 flex-none text-accent" />
            ) : (
              <Attention taille={18} className="mt-0.75 flex-none text-alerte" />
            )}
            {insecables(message.texte)}
          </p>
        ) : (
          <Contenu message={message} />
        )}
      </div>
    </li>
  );
}

const LIBELLE_STATUT: Record<StatutCarte, string> = {
  attente: "En attente de votre accord",
  envoyee: "Envoi…",
  confirmee: "Confirmé",
  annulee: "Annulé",
  refusee: "Refusé par la banque",
  remplacee: "Remplacée",
  expiree: "Plus valable",
  erreur: "À vérifier",
};

/** La carte « Wach nconfirmi ? » de la maquette : l'opération vérifiée à blanc, et les boutons tant qu'elle attend. */
function CarteConfirmation({ carte, repondre }: { carte: Carte; repondre: (reponse: "Oui" | "Non") => void }) {
  const paiement = carte.type === "paiement";
  const lignes: [string, string, boolean?][] = paiement
    ? [
        ["Fournisseur", carte.fournisseur ?? ""],
        ["Montant", dh(carte.montant), true],
        ["Solde après paiement", dh(carte.nouveau_solde)],
      ]
    : [
        ["Bénéficiaire", carte.beneficiaire ?? ""],
        ["RIB du bénéficiaire", carte.beneficiaire_rib_masque ?? ""],
        ["Montant", dh(carte.montant), true],
        ["Solde après virement", dh(carte.nouveau_solde)],
      ];
  const attente = carte.statut === "attente";
  const eteinte = ["annulee", "remplacee", "expiree"].includes(carte.statut);
  const bordure = attente ? "border-accent" : carte.statut === "refusee" ? "border-[#8a6a2e]" : "border-bordure";
  const pastille =
    carte.statut === "refusee"
      ? "border-[#8a6a2e] bg-[#2b2720] text-[#f5cb80]"
      : eteinte
        ? "border-bordure-forte bg-[#2a2c30] text-attenue"
        : "border-[#4a4e35] bg-surligne text-note-texte";
  return (
    <section
      aria-label={paiement ? "Paiement de facture" : "Virement"}
      className={`flex flex-col gap-3 rounded-[18px] border-[1.5px] bg-surface p-4 ${bordure} ${eteinte ? "opacity-75" : ""}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 text-[15px] font-semibold">
          {paiement ? <Recu taille={18} className="text-accent" /> : <Echange taille={18} className="text-accent" />}
          {paiement ? "Paiement de facture" : "Virement"}
        </h3>
        <span className={`rounded-full border px-2.5 py-0.75 text-xs font-medium ${pastille}`}>
          {LIBELLE_STATUT[carte.statut]}
        </span>
      </div>
      <dl className="flex flex-col text-sm">
        {lignes.map(([terme, valeur, fort]) => (
          <div key={terme} className="flex items-baseline justify-between gap-2.5 border-t border-[#36393e] py-1.75">
            <dt className="text-attenue">{terme}</dt>
            <dd className={`text-right tabular-nums ${fort ? "text-xl font-semibold text-accent" : "font-semibold"}`}>
              {valeur}
            </dd>
          </div>
        ))}
      </dl>
      {attente && (
        <>
          <p dir="auto" className="text-[15.5px] font-medium">
            {carte.question}
          </p>
          <div className="flex gap-2.5">
            <button
              type="button"
              onClick={() => repondre("Oui")}
              className="min-h-11 flex-1 cursor-pointer rounded-full bg-accent text-sm font-semibold text-sur-accent"
            >
              Oui, confirmer
            </button>
            <button
              type="button"
              onClick={() => repondre("Non")}
              className="min-h-11 flex-1 cursor-pointer rounded-full border-[1.5px] border-[#5a5d62] text-sm font-semibold"
            >
              Non, annuler
            </button>
          </div>
          <p className="flex items-center gap-2 text-xs text-attenue">
            <Cadenas taille={14} />
            Rien ne bouge sur votre compte tant que vous n&apos;avez pas confirmé.
          </p>
        </>
      )}
    </section>
  );
}

function Contenu({ message }: { message: MessageWakil }) {
  const intro = message.texte.split("\n")[0]; // « Hahoma akhir l'opérations dyalek : »
  if (message.donnees != null) {
    switch (message.outil) {
      case "consulter_solde": {
        const { solde } = message.donnees as { solde: string };
        return (
          <>
            <p>Solde dyalek howa</p>
            <p className="text-[26px] font-semibold tracking-[0.01em] text-accent tabular-nums">{dh(solde)}</p>
          </>
        );
      }
      case "lister_transactions": {
        const operations = message.donnees as Operation[];
        return (
          <>
            <p className="mb-1.5">{intro}</p>
            <ul className="text-sm">
              {operations.map((o) => (
                <li key={o.id} className="grid grid-cols-[42px_minmax(0,1fr)_auto] gap-2.5 border-t border-[#3a3d42] py-2">
                  <span className="text-attenue tabular-nums">{jour(o.date)}</span>
                  <span>{o.libelle}</span>
                  <span className="text-right tabular-nums">{montantSigne(o.montant)}</span>
                </li>
              ))}
            </ul>
          </>
        );
      }
      case "lister_factures": {
        const factures = message.donnees as Facture[];
        if (factures.length === 0) break; // « Ma 3ndek hta facture… » : le texte suffit
        return (
          <>
            <p className="mb-1.5">{intro}</p>
            <ul className="text-sm">
              {factures.map((f) => (
                <li key={f.id} className="flex justify-between gap-3 border-t border-[#3a3d42] py-2">
                  <span>{f.fournisseur}</span>
                  <span className="font-semibold tabular-nums">{dh(f.montant)}</span>
                </li>
              ))}
            </ul>
          </>
        );
      }
    }
  }
  return (
    <p dir="auto" className="whitespace-pre-line">
      {insecables(message.texte)}
    </p>
  );
}

/** Pendant la réponse : Wakil lit la demande (le LLM), puis interroge la banque. */
export function IndicateurAvancement({ etat }: { etat: Exclude<Avancement, null> }) {
  return (
    <li className="flex">
      <div className={`${BULLE} flex flex-col gap-2 rounded-bl-md bg-surface-2 text-sm`}>
        {etat === "banque" && (
          <p className="flex items-center gap-2.5 text-attenue">
            <Coche taille={16} className="text-accent" />
            Fhemt talab dyalek
          </p>
        )}
        <p className="flex items-center gap-2.5">
          <Points />
          {etat === "lecture" ? "Kanqra talab dyalek…" : "Kanchouf f la banque…"}
        </p>
      </div>
    </li>
  );
}

function Points() {
  return (
    <span aria-hidden="true" className="flex w-4 justify-center gap-0.75">
      {["", "[animation-delay:200ms]", "[animation-delay:400ms]"].map((delai) => (
        <span key={delai} className={`size-1 animate-pulse rounded-full bg-accent motion-reduce:animate-none ${delai}`} />
      ))}
    </span>
  );
}

/** La session de démo dure 30 minutes : passé ce délai, on invite à choisir à nouveau un client. */
export function SessionExpiree() {
  return (
    <li role="alert" className="flex flex-col gap-3 rounded-[20px] border border-bordure bg-surface p-4 text-sm">
      <p className="flex items-center gap-2 font-semibold">
        <Cadenas taille={18} className="text-accent" />
        Votre session a expiré
      </p>
      <p className="leading-relaxed text-attenue">
        Une session de démo dure 30 minutes. Choisissez à nouveau un client pour reprendre la discussion.
      </p>
      <Link
        href="/"
        className="inline-flex min-h-11 items-center self-start rounded-full bg-accent px-5 font-semibold text-sur-accent"
      >
        Revenir à l&apos;accueil
      </Link>
    </li>
  );
}
