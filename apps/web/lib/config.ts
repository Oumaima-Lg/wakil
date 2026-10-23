// Adresse d'agent-api vue par le serveur Next.js : en local le port 8001, en ligne une variable d'environnement.
export const AGENT_API_URL = process.env.AGENT_API_URL ?? "http://127.0.0.1:8001";
