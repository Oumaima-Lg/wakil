"use client";

import { useEffect, useRef, useState } from "react";

import { Deplier, Etoile, Fleche } from "@/components/icones";

import { AccueilChat, BulleClient, BulleWakil, IndicateurAvancement, SessionExpiree } from "./Bulles";
import { useEspace } from "./ContexteEspace";
import { useConversation } from "./useConversation";

/**
 * Le panneau de Wakil, à droite. Fermé, il est seulement caché (hidden) : la conversation et le brouillon
 * restent en mémoire quand on le ferme ou qu'on change de page.
 */
export function PanneauWakil() {
  const { espace, wakilOuvert, setWakilOuvert } = useEspace();
  const { messages, avancement, sessionExpiree, envoyer, reessayer } = useConversation();
  const [brouillon, setBrouillon] = useState("");
  const zone = useRef<HTMLDivElement>(null);
  const champ = useRef<HTMLTextAreaElement>(null);

  // À l'ouverture du panneau, le curseur se place dans le champ de saisie.
  useEffect(() => {
    if (wakilOuvert) champ.current?.focus();
  }, [wakilOuvert]);

  // Chaque nouveau message (ou nouvelle étape) fait défiler la conversation jusqu'en bas.
  useEffect(() => {
    zone.current?.scrollTo({ top: zone.current.scrollHeight, behavior: "smooth" });
  }, [messages, avancement]);

  function soumettre(evenement: { preventDefault: () => void }) {
    evenement.preventDefault();
    if (envoyer(brouillon)) setBrouillon("");
  }

  function touche(evenement: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Entrée envoie, Maj+Entrée va à la ligne. isComposing : un mot est en cours de saisie (clavier arabe, IME).
    if (evenement.key === "Enter" && !evenement.shiftKey && !evenement.nativeEvent.isComposing) soumettre(evenement);
  }

  return (
    <>
      {!wakilOuvert && (
        <button
          type="button"
          onClick={() => setWakilOuvert(true)}
          className="fixed right-7 bottom-7 z-10 inline-flex min-h-14 cursor-pointer items-center gap-2.5 rounded-full bg-accent pr-6 pl-5 font-semibold text-sur-accent shadow-[0_18px_50px_-12px_#000000aa]"
        >
          <Etoile taille={22} />
          Wakil
        </button>
      )}

      <aside
        hidden={!wakilOuvert}
        aria-label="Wakil, assistant en darija"
        className="flex w-96 flex-none flex-col border-l border-[#2e3034] bg-[#202125]"
      >
        <div className="flex items-center justify-between gap-3 border-b border-surface-2 py-4 pr-4 pl-5">
          <div className="flex items-center gap-2.5">
            <Etoile taille={26} className="text-accent" />
            <div className="flex flex-col">
              <span className="text-[17px] font-semibold tracking-wide text-accent">Wakil</span>
              <span className="text-[12.5px] text-attenue">Votre assistant en darija</span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setWakilOuvert(false)}
            aria-label="Fermer Wakil"
            className="flex size-11 cursor-pointer items-center justify-center rounded-xl border border-bordure-forte text-texte-2 hover:border-accent"
          >
            <Deplier taille={18} />
          </button>
        </div>

        {/* Seule cette zone défile : la saisie reste en bas, toujours visible */}
        <div ref={zone} className="flex min-h-0 flex-1 flex-col overflow-y-auto px-4.5 py-5.5">
          {messages.length === 0 && !sessionExpiree ? (
            <AccueilChat prenom={espace?.profil.prenom ?? ""} envoyer={envoyer} />
          ) : (
            // aria-live : un lecteur d'écran annonce chaque nouvelle réponse
            <ol aria-label="Conversation" aria-live="polite" className="flex flex-col gap-4">
              {messages.map((message) =>
                message.auteur === "client" ? (
                  <BulleClient key={message.id} texte={message.texte} />
                ) : (
                  <BulleWakil key={message.id} message={message} reessayer={() => reessayer(message)} />
                ),
              )}
              {avancement && <IndicateurAvancement etat={avancement} />}
              {sessionExpiree && <SessionExpiree />}
            </ol>
          )}
        </div>

        <form onSubmit={soumettre} className="border-t border-surface-2 px-4 pt-3 pb-4.5">
          <label htmlFor="message-wakil" className="sr-only">
            Votre message à Wakil
          </label>
          <div className="flex items-end gap-2 rounded-3xl border border-bordure-forte bg-surface py-1.5 pr-1.5 pl-4 focus-within:border-accent">
            <textarea
              ref={champ}
              id="message-wakil"
              rows={1}
              maxLength={500}
              dir="auto"
              value={brouillon}
              onChange={(e) => setBrouillon(e.target.value)}
              onKeyDown={touche}
              placeholder="Ktab hna…"
              className="field-sizing-content max-h-32 min-h-6.5 flex-1 resize-none bg-transparent py-2.25 text-[15px] leading-normal placeholder:text-faible focus:outline-none"
            />
            <button
              type="submit"
              aria-label="Envoyer"
              disabled={!brouillon.trim() || avancement !== null || sessionExpiree}
              className="flex size-11 flex-none cursor-pointer items-center justify-center rounded-full bg-accent text-sur-accent disabled:cursor-not-allowed disabled:opacity-45"
            >
              <Fleche taille={18} />
            </button>
          </div>
          <p className="mt-2 px-1 text-xs text-faible">Les montants viennent toujours de la banque, jamais de l&apos;IA.</p>
        </form>
      </aside>
    </>
  );
}
