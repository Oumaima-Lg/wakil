# web — le front de Wakil (Next.js)

Interface de la Banque Atlas Démo et de son assistant Wakil. **Données 100 % fictives – projet de démonstration.**

Lancer en local (bank-api sur le port 8000 et agent-api sur le port 8001 doivent tourner) :

```bash
npm run dev
```

Puis ouvrir http://localhost:3000. Les appels `/api/…` sont transmis à agent-api (voir `next.config.ts`).
L'adresse d'agent-api (`AGENT_API_URL`, par défaut `http://127.0.0.1:8001`) est lue **au build** : la changer
demande de reconstruire le site.

Vérifier le code : `npm run lint` et `npm run typecheck` (qui génère d'abord les types des routes avec `next typegen`).
