import { useSyncExternalStore } from "react";

// Le point de bascule « lg » de Tailwind : à partir de 1024 px, menu à gauche et Wakil en panneau à droite.
const REQUETE = "(min-width: 64rem)";

function abonner(prevenir: () => void) {
  const requete = window.matchMedia(REQUETE);
  requete.addEventListener("change", prevenir);
  return () => requete.removeEventListener("change", prevenir);
}

/**
 * true sur un grand écran, false sur un téléphone ou une petite tablette ; se met à jour si la fenêtre change de taille.
 * (≈ BreakpointObserver du CDK Angular.) Le rendu serveur ne connaît pas l'écran : il suppose un grand écran.
 */
export function useEcranLarge(): boolean {
  return useSyncExternalStore(
    abonner,
    () => window.matchMedia(REQUETE).matches,
    () => true,
  );
}
