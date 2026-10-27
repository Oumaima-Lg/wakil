import { PORTAIL_API_URL } from "@/lib/config";

import { CarteClientDemo, type ClientDemo } from "./CarteClientDemo";

/**
 * Composant serveur (pas de « use client ») : il s'exécute sur le serveur Next.js, lit les clients de démo dans
 * portail-api, et envoie au navigateur du HTML déjà rempli. Le navigateur ne voit jamais l'adresse de portail-api.
 */
export async function ListeClientsDemo() {
  let clients: ClientDemo[];
  try {
    const reponse = await fetch(`${PORTAIL_API_URL}/clients-demo`);
    if (!reponse.ok) throw new Error(String(reponse.status));
    clients = await reponse.json();
  } catch {
    return (
      <p role="alert" className="rounded-2xl border border-bordure bg-surface p-6 text-attenue">
        La banque de démo est momentanément indisponible. Réessayez dans un instant.
      </p>
    );
  }
  return (
    <div className="flex flex-wrap gap-6">
      {clients.map((client) => (
        <CarteClientDemo key={client.id} client={client} />
      ))}
    </div>
  );
}

/** Affiché pendant le chargement, grâce à <Suspense> (voir app/page.tsx). */
export function ListeClientsDemoChargement() {
  return (
    <div className="flex flex-wrap gap-6" aria-busy="true" aria-label="Chargement des clients de démo">
      {[1, 2, 3].map((n) => (
        <div key={n} className="h-[360px] flex-[1_1_300px] animate-pulse rounded-3xl border border-bordure bg-surface" />
      ))}
    </div>
  );
}
