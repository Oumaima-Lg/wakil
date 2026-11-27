import type { NextConfig } from "next";

import { AGENT_API_URL, PORTAIL_API_URL } from "./lib/config";

const nextConfig: NextConfig = {
  // « next build » produit aussi un serveur autonome (.next/standalone), avec seulement les fichiers utiles : c'est
  // lui que lance l'image Docker (apps/web/Dockerfile). Sans effet sur « next dev ».
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
  // Le bouton « N » des outils de Next (en développement seulement). Par défaut en bas à gauche, il cacherait
  // « Se déconnecter » du menu ; fixé ici pour tout le monde, et pas seulement dans le cache .next de chacun.
  devIndicators: { position: "top-right" },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // Le navigateur appelle /api/… sur l'adresse du site, et Next.js transmet au bon service (comme le proxy.conf.json
  // d'Angular) : le chat à agent-api, tout le reste (session, pages) à portail-api. Une seule adresse pour le
  // navigateur : le cookie de session HttpOnly marche sans régler de CORS. La première règle qui correspond gagne.
  async rewrites() {
    return [
      { source: "/api/chat", destination: `${AGENT_API_URL}/chat` },
      { source: "/api/:chemin*", destination: `${PORTAIL_API_URL}/:chemin*` },
    ];
  },
};

export default nextConfig;
