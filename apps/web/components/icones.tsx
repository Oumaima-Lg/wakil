// Icônes au trait de la maquette. Décoratives : aria-hidden, le texte à côté porte le sens.
type Props = { taille?: number; className?: string };

function Svg({ taille = 20, className, children, ...reste }: Props & React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      width={taille}
      height={taille}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
      {...reste}
    >
      {children}
    </svg>
  );
}

/** Le logo de Wakil : une étoile à 8 branches. */
export function Etoile(props: Props) {
  return (
    <Svg strokeWidth={1.5} {...props}>
      <rect x="5.5" y="5.5" width="13" height="13" />
      <rect x="5.5" y="5.5" width="13" height="13" transform="rotate(45 12 12)" />
    </Svg>
  );
}

/** Le logo de la Banque Atlas Démo : des montagnes. */
export function Montagnes(props: Props) {
  return (
    <Svg strokeWidth={1.5} {...props}>
      <path d="M2.5 19.5l6.5-11 4.2 6.6 2.3-3.4 6 7.8z" />
    </Svg>
  );
}

export function Info(props: Props) {
  return (
    <Svg strokeWidth={1.8} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6M12 7.5v.01" />
    </Svg>
  );
}

export function Code(props: Props) {
  return (
    <Svg strokeWidth={1.8} {...props}>
      <path d="M8 7l-5 5 5 5M16 7l5 5-5 5" />
    </Svg>
  );
}

export function Fleche(props: Props) {
  return (
    <Svg strokeWidth={2} {...props}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </Svg>
  );
}

export function Lignes(props: Props) {
  return (
    <Svg strokeWidth={1.6} {...props}>
      <path d="M4 7h16M4 12h16M4 17h10" />
    </Svg>
  );
}

export function Cadenas(props: Props) {
  return (
    <Svg strokeWidth={1.6} {...props}>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </Svg>
  );
}

export function Coche(props: Props) {
  return (
    <Svg strokeWidth={1.6} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12.5l2.7 2.7L16 9.8" />
    </Svg>
  );
}

export function Grille(props: Props) {
  return (
    <Svg strokeWidth={1.7} {...props}>
      <rect x="4" y="4" width="7" height="7" rx="1.5" />
      <rect x="13" y="4" width="7" height="7" rx="1.5" />
      <rect x="4" y="13" width="7" height="7" rx="1.5" />
      <rect x="13" y="13" width="7" height="7" rx="1.5" />
    </Svg>
  );
}

export function Liste(props: Props) {
  return (
    <Svg strokeWidth={1.7} {...props}>
      <path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01" />
    </Svg>
  );
}

export function Recu(props: Props) {
  return (
    <Svg strokeWidth={1.7} {...props}>
      <path d="M6 3h12v18l-3-2-3 2-3-2-3 2z" />
      <path d="M9 8h6M9 12h6" />
    </Svg>
  );
}

export function Personnes(props: Props) {
  return (
    <Svg strokeWidth={1.7} {...props}>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      <path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5c1.8.8 3 2.7 3 5.5" />
    </Svg>
  );
}

export function CarteBancaire(props: Props) {
  return (
    <Svg strokeWidth={1.7} {...props}>
      <rect x="3" y="6" width="18" height="12" rx="2.5" />
      <path d="M3 10h18" />
    </Svg>
  );
}

export function Replier(props: Props) {
  return (
    <Svg strokeWidth={1.8} {...props}>
      <path d="M11 7l-5 5 5 5M18 7l-5 5 5 5" />
    </Svg>
  );
}

export function Deplier(props: Props) {
  return (
    <Svg strokeWidth={1.8} {...props}>
      <path d="M13 7l5 5-5 5M6 7l5 5-5 5" />
    </Svg>
  );
}

export function Goutte(props: Props) {
  return (
    <Svg strokeWidth={1.7} {...props}>
      <path d="M12 3.5c3.5 4.2 6 7.6 6 10.5a6 6 0 0 1-12 0c0-2.9 2.5-6.3 6-10.5z" />
    </Svg>
  );
}

export function Wifi(props: Props) {
  return (
    <Svg strokeWidth={1.7} {...props}>
      <path d="M3.5 9.5a12 12 0 0 1 17 0M6.5 12.8a7.7 7.7 0 0 1 11 0M9.5 16a3.5 3.5 0 0 1 5 0M12 19.2v.01" />
    </Svg>
  );
}

export function Mobile(props: Props) {
  return (
    <Svg strokeWidth={1.7} {...props}>
      <rect x="7" y="3" width="10" height="18" rx="2.5" />
      <path d="M11 17.5h2" />
    </Svg>
  );
}

export function Recherche(props: Props) {
  return (
    <Svg strokeWidth={1.8} {...props}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="M16 16l4 4" />
    </Svg>
  );
}
