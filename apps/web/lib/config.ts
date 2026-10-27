// Adresses des services vues par le serveur Next.js : en local les ports 8001 et 8003, en ligne des variables
// d'environnement. Le navigateur ne les voit jamais.
export const AGENT_API_URL = process.env.AGENT_API_URL ?? "http://127.0.0.1:8001";
export const PORTAIL_API_URL = process.env.PORTAIL_API_URL ?? "http://127.0.0.1:8003";
