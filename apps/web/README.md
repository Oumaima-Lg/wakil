# web — le front de Wakil (Next.js)

Interface de la Banque Atlas Démo et de son assistant Wakil. **Données 100 % fictives – projet de démonstration.**

Lancer en local (portail-api sur le port 8003 et agent-api sur le port 8001 doivent tourner, voir le README à la racine) :

```bash
npm run dev
```

Puis ouvrir http://localhost:3000. Le front n'a que l'interface : `/api/chat` est transmis à agent-api, et le reste de
`/api/…` (session, pages de l'espace) à portail-api (voir `next.config.ts`). Les adresses (`AGENT_API_URL`, par défaut
`http://127.0.0.1:8001` ; `PORTAIL_API_URL`, par défaut `http://127.0.0.1:8003`) sont lues **au build** : les changer
demande de reconstruire le site.

Vérifier le code : `npm run lint` et `npm run typecheck` (qui génère d'abord les types des routes avec `next typegen`).
