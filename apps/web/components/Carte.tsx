import { Montagnes } from "./icones";

type Props = {
  titulaire: string;
  fin: string; // 4 derniers chiffres du compte
  civilite: "madame" | "monsieur";
  expiration?: string;
  className?: string; // la largeur : 340 px par défaut, moins si la place manque
};

/**
 * Mesure de la maquette (dessinée sur 340 px de large), mise à l'échelle de la largeur réelle de la carte :
 * u(18) vaut 18 px quand la carte fait 340 px, 9 px quand elle en fait 170. 100cqw = la largeur de la carte (@container).
 */
const u = (px: number) => `calc(${px} * 100cqw / 340)`;

/** La carte de démo, aux couleurs de l'app (maquette 4B) : « DÉMO » à la place d'un vrai réseau de paiement. */
export function Carte({ titulaire, fin, civilite, expiration = "10/29", className = "w-[340px] max-w-full" }: Props) {
  return (
    <div
      role="img"
      aria-label={`Carte bancaire de démo de ${titulaire}, se terminant par ${fin}`}
      className={`@container relative aspect-[340/214] flex-none overflow-hidden rounded-[5.3%/8.4%] border border-[#4a4f2c] bg-[#202217] shadow-[0_24px_60px_-26px_#000000cc] ${className}`}
    >
      {civilite === "madame" ? <Femme /> : <Homme />}

      <div className="absolute flex items-center" style={{ top: u(18), left: u(20), gap: u(8) }}>
        <Montagnes className="text-accent" style={{ width: u(24), height: u(24) }} />
        <span className="font-semibold tracking-wide" style={{ fontSize: u(13) }}>
          Banque Atlas
        </span>
      </div>
      <div className="absolute flex items-center" style={{ top: u(70), left: u(20), gap: u(12) }} aria-hidden="true">
        <svg viewBox="0 0 42 32" style={{ width: u(42), height: u(32) }}>
          <rect x="0.75" y="0.75" width="40.5" height="30.5" rx="6" fill="#4A4F2C" stroke="#D7F25C" strokeOpacity="0.7" strokeWidth="1.5" />
          <path
            d="M14 1v30M28 1v30M1 11h13M28 11h13M1 21h13M28 21h13M14 16h14"
            stroke="#D7F25C"
            strokeOpacity="0.55"
            strokeWidth="1.2"
            fill="none"
          />
        </svg>
        <svg viewBox="0 0 24 24" fill="none" stroke="#D3D6CF" strokeWidth="1.6" strokeLinecap="round" style={{ width: u(22), height: u(22) }}>
          <path d="M8 8.5c1.2 2.2 1.2 4.8 0 7M11.5 6.5c2 3.4 2 7.6 0 11M15 4.5c2.8 4.6 2.8 10.4 0 15" />
        </svg>
      </div>
      <p className="absolute tracking-[0.14em] tabular-nums" style={{ top: u(122), left: u(20), fontSize: u(16) }}>
        •••• •••• •••• {fin}
      </p>
      <div className="absolute flex" style={{ bottom: u(16), left: u(20), gap: u(22) }}>
        <div className="flex flex-col">
          <span className="tracking-[0.16em] text-attenue uppercase" style={{ fontSize: u(9.5) }}>
            Titulaire
          </span>
          <span className="font-medium tracking-[0.1em] uppercase" style={{ fontSize: u(12.5) }}>
            {titulaire}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="tracking-[0.16em] text-attenue uppercase" style={{ fontSize: u(9.5) }}>
            Expire
          </span>
          <span className="font-medium tracking-[0.1em]" style={{ fontSize: u(12.5) }}>
            {expiration}
          </span>
        </div>
      </div>
      <span
        className="absolute rounded-md bg-sur-accent font-bold tracking-[0.14em] text-accent italic"
        style={{ top: u(16), right: u(16), padding: `${u(2)} ${u(8)}`, fontSize: u(11) }}
      >
        DÉMO
      </span>
    </div>
  );
}

const PERSONNAGE = { right: u(-10), bottom: u(-14), width: u(160), height: u(192) };

function Femme() {
  return (
    <svg viewBox="0 0 200 240" className="absolute" style={PERSONNAGE} aria-hidden="true">
      <circle cx="100" cy="118" r="92" fill="#D7F25C" fillOpacity="0.14" />
      <path d="M60 96 C56 52 78 30 102 30 C128 30 148 54 144 96 C143 116 148 132 156 146 L46 146 C54 132 61 116 60 96 Z" fill="#2B1F1B" />
      <rect x="89" y="112" width="24" height="30" rx="6" fill="#A86C48" />
      <path d="M34 240 C34 184 58 152 90 142 L101 164 L112 142 C144 152 168 184 168 240 Z" fill="#3A3F25" />
      <path d="M90 142 L101 172 L112 142 C106 139 96 139 90 142 Z" fill="#F1F2EE" />
      <path d="M90 142 L82 176 L101 168 M112 142 L120 176 L101 168" fill="none" stroke="#D7F25C" strokeWidth="2" strokeLinejoin="round" />
      <ellipse cx="101" cy="88" rx="27" ry="32" fill="#C68A62" />
      <path d="M72 84 C74 56 94 46 117 49 C133 52 140 66 132 80 C118 70 97 67 72 84 Z" fill="#2B1F1B" />
      <ellipse cx="91" cy="91" rx="2.6" ry="3.2" fill="#2B1F1B" />
      <ellipse cx="111" cy="91" rx="2.6" ry="3.2" fill="#2B1F1B" />
      <path d="M86 83 q5 -3 10 0 M106 83 q5 -3 10 0" fill="none" stroke="#2B1F1B" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M93 104 q8 6 16 0" fill="none" stroke="#7A3E2A" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="74" cy="98" r="3" fill="#D7F25C" />
      <circle cx="128" cy="98" r="3" fill="#D7F25C" />
      <Telephone peau="#C68A62" />
    </svg>
  );
}

function Homme() {
  return (
    <svg viewBox="0 0 200 240" className="absolute" style={PERSONNAGE} aria-hidden="true">
      <circle cx="100" cy="118" r="92" fill="#D7F25C" fillOpacity="0.14" />
      <rect x="89" y="110" width="24" height="32" rx="6" fill="#9C6440" />
      <path d="M34 240 C34 184 58 152 90 142 L101 164 L112 142 C144 152 168 184 168 240 Z" fill="#3A3F25" />
      <path d="M90 142 L101 172 L112 142 C106 139 96 139 90 142 Z" fill="#F1F2EE" />
      <path d="M97.5 146 L104.5 146 L106 166 L101 174 L96 166 Z" fill="#D7F25C" />
      <path d="M90 142 L82 176 L101 168 M112 142 L120 176 L101 168" fill="none" stroke="#D7F25C" strokeWidth="2" strokeLinejoin="round" />
      <ellipse cx="75" cy="92" rx="5" ry="8" fill="#B97B55" />
      <ellipse cx="127" cy="92" rx="5" ry="8" fill="#B97B55" />
      <ellipse cx="101" cy="88" rx="26" ry="31" fill="#B97B55" />
      <path d="M75 84 C71 56 88 42 105 43 C122 44 133 57 128 84 C125 70 116 63 102 63 C89 63 79 70 75 84 Z" fill="#1F1714" />
      <path d="M79 98 C81 117 91 125 101 125 C111 125 121 117 123 98 C119 110 111 115 101 115 C91 115 83 110 79 98 Z" fill="#1F1714" fillOpacity="0.9" />
      <ellipse cx="91" cy="90" rx="2.6" ry="3.2" fill="#1F1714" />
      <ellipse cx="111" cy="90" rx="2.6" ry="3.2" fill="#1F1714" />
      <path d="M85 82 q6 -3 12 0 M105 82 q6 -3 12 0" fill="none" stroke="#1F1714" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M94 104 q7 5 14 0" fill="none" stroke="#5A3524" strokeWidth="2.2" strokeLinecap="round" />
      <Telephone peau="#B97B55" />
    </svg>
  );
}

/** Le bras et le téléphone, communs aux deux personnages. */
function Telephone({ peau }: { peau: string }) {
  return (
    <>
      <path d="M146 170 C158 190 154 214 132 222 L122 206 C136 200 138 190 132 180 Z" fill="#33381F" />
      <rect x="104" y="172" width="28" height="46" rx="6" fill="#16170F" />
      <rect x="108" y="178" width="20" height="32" rx="3" fill="#D7F25C" fillOpacity="0.85" />
      <ellipse cx="128" cy="204" rx="9" ry="7" fill={peau} />
    </>
  );
}
