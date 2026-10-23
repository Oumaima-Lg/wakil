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
