import type { NextConfig } from "next";

import { AGENT_API_URL } from "./lib/config";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // Le navigateur appelle /api/… sur l'adresse du site, et Next.js transmet à agent-api (comme le proxy.conf.json
  // d'Angular). Une seule adresse pour le navigateur : le cookie de session HttpOnly marche sans régler de CORS.
  async rewrites() {
    return [{ source: "/api/:chemin*", destination: `${AGENT_API_URL}/:chemin*` }];
  },
};

export default nextConfig;
