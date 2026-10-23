import Link from "next/link";
import { Suspense } from "react";

import { ListeClientsDemo, ListeClientsDemoChargement } from "@/components/ListeClientsDemo";
import { Cadenas, Code, Coche, Etoile, Fleche, Lignes } from "@/components/icones";

const DEPOT = "https://github.com/Oumaima-Lg/wakil";

const GARANTIES = [
  {
    Icone: Lignes,
    titre: "Les montants viennent de la banque",
    texte: "Aucun chiffre n'est inventé par l'IA : soldes et factures sont lus dans la banque fictive.",
  },
  {
    Icone: Cadenas,
    titre: "Votre compte, et seulement le vôtre",
    texte: "Chaque demande est vérifiée par la banque : impossible de lire le compte d'un autre client.",
  },
  {
    Icone: Coche,
    titre: "Confirmation avant chaque opération",
    texte: "Avant un paiement ou un virement, Wakil demande toujours « Wach nconfirmi ? ».",
  },
];

export default function Accueil() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6">
      <header className="flex flex-wrap items-center justify-between gap-4 pt-7 pb-3">
        <Link href="/" aria-label="Wakil, accueil" className="flex items-center gap-3 text-accent">
          <Etoile taille={34} />
          <span className="text-3xl font-semibold tracking-wider">Wakil</span>
          <span lang="ar" dir="rtl" className="font-arabe text-xl text-attenue">
            وكيل
          </span>
        </Link>
        <a href={DEPOT} className="flex items-center gap-2 font-medium tracking-wide">
          <Code taille={18} className="text-accent" />
          Code source
        </a>
      </header>

      <div className="relative h-10" aria-hidden="true">
        <svg viewBox="0 0 1000 40" preserveAspectRatio="none" className="absolute inset-0 size-full text-accent">
          <polyline
            points="0,1 330,1 360,39 640,39 670,1 1000,1"
            fill="none"
            stroke="currentColor"
            strokeOpacity="0.7"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <p className="relative text-center text-[13px] leading-[38px] font-medium tracking-[0.24em] text-attenue uppercase">
          Banque Atlas Démo
        </p>
      </div>

      <section className="flex flex-wrap items-center gap-14 pt-16 pb-22">
        <div className="flex min-w-0 flex-[1_1_480px] flex-col gap-6">
          <p className="tracking-[0.12em] text-attenue uppercase">Assistant bancaire en darija</p>
          <h1 className="text-[clamp(40px,5.6vw,68px)] leading-[1.06] font-semibold text-accent">
            Parlez à votre banque en darija.
          </h1>
          <p className="max-w-xl text-lg leading-relaxed text-texte-2">
            Wakil comprend vos questions écrites en lettres arabes, en lettres latines ou mélangées au français, et vous
            répond avec les données de votre compte de démo.
          </p>
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-sm text-attenue">Par exemple :</span>
            <span dir="auto" className="rounded-full border border-bordure-forte px-3.5 py-2 text-[15px]">
              chhal bqa f compte dyali ?
            </span>
            <span lang="ar" dir="rtl" className="rounded-full border border-bordure-forte px-3.5 py-2 font-arabe">
              شحال بقا فالحساب ديالي؟
            </span>
            <span dir="auto" className="rounded-full border border-bordure-forte px-3.5 py-2 text-[15px]">
              bghit nchouf les factures dyali
            </span>
          </div>
          <div className="flex flex-wrap gap-4 pt-3">
            <a
              href="#clients"
              className="inline-flex min-h-13 items-center rounded-full bg-accent px-7 font-semibold tracking-wide text-sur-accent"
            >
              Choisir un client de démo
            </a>
            <a
              href={DEPOT}
              className="inline-flex min-h-13 items-center rounded-full border-[1.5px] border-accent px-7 font-semibold tracking-wide"
            >
              Voir le code source
            </a>
          </div>
        </div>

        <ApercuConversation />
      </section>

      <section id="clients" className="flex scroll-mt-6 flex-col gap-7 pb-22">
        <div className="flex flex-col gap-2.5">
          <h2 className="text-[clamp(26px,3vw,34px)] font-semibold">Choisissez un client de démo</h2>
          <p className="text-[17px] text-attenue">Chaque client teste un scénario différent. Toutes ses données sont inventées.</p>
        </div>
        {/* Les données arrivent d'agent-api : en attendant, Suspense affiche des cartes grises. */}
        <Suspense fallback={<ListeClientsDemoChargement />}>
          <ListeClientsDemo />
        </Suspense>
      </section>

      <section aria-label="Garanties" className="flex flex-wrap gap-6 border-t border-surface-2 pt-10 pb-18">
        {GARANTIES.map(({ Icone, titre, texte }) => (
          <div key={titre} className="flex min-w-0 flex-[1_1_280px] gap-4">
            <Icone taille={28} className="flex-none text-accent" />
            <div className="flex flex-col gap-1.5">
              <h3 className="font-semibold">{titre}</h3>
              <p className="text-[15px] leading-relaxed text-attenue">{texte}</p>
            </div>
          </div>
        ))}
      </section>

      <footer className="flex flex-wrap justify-between gap-3 border-t border-surface-2 pt-6 pb-10 text-sm text-attenue">
        <p>Wakil · 2026</p>
        <p>Données 100 % fictives – projet de démonstration</p>
      </footer>
    </div>
  );
}

/** Le téléphone de l'accueil : une vraie conversation de Wakil (réponses réelles de l'agent avec les données de Salma). */
function ApercuConversation() {
  const client = "self-end max-w-[82%] rounded-[18px_18px_4px_18px] bg-accent px-3.5 py-2.5 text-[13.5px] text-sur-accent";
  const wakil = "self-start max-w-[90%] rounded-[18px_18px_18px_4px] bg-surface-2 px-3.5 py-2.5 text-[13.5px]";
  return (
    <div className="mx-auto flex min-w-0 flex-[0_1_330px] justify-center">
      <div
        role="img"
        aria-label="Aperçu d'une conversation avec Wakil"
        className="w-[310px] max-w-full rounded-[44px] border border-bordure-forte bg-[#141517] p-3 shadow-[0_0_0_1px_#D7F25C26,0_30px_90px_-30px_#D7F25C59]"
      >
        <div className="flex min-h-[540px] flex-col gap-3 rounded-[34px] bg-[#202125] px-3.5 py-4.5">
          <div className="flex items-center gap-2 border-b border-surface-2 px-1 pb-3">
            <Etoile taille={18} className="text-accent" />
            <span className="text-[15px] font-semibold">Wakil</span>
            <span className="text-[13px] text-attenue">· Salma</span>
          </div>
          <p dir="auto" className={client}>
            Salam, chhal bqa f compte dyali ?
          </p>
          <p dir="auto" className={wakil}>
            Solde dyalek howa 2 350 DH.
          </p>
          <p lang="ar" dir="rtl" className={`${client} font-arabe text-[14.5px]`}>
            واش عندي شي فاتورة ما خلصتهاش؟
          </p>
          <p dir="auto" className={`${wakil} whitespace-pre-line`}>
            {"3ndek 2 factures mazal ma tkhelsou (561 DH f lmjmou3) :\n- Eau & Électricité (démo) : 312 DH\n- Internet (démo) : 249 DH"}
          </p>
          <div className="mt-auto flex items-center gap-2 rounded-full border border-bordure-forte py-1.5 pr-1.5 pl-3.5">
            <span className="flex-1 text-[13px] text-faible">Ktab hna…</span>
            <span className="flex size-[34px] items-center justify-center rounded-full bg-accent text-sur-accent">
              <Fleche taille={16} />
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
