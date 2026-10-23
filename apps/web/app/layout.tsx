import type { Metadata } from "next";
import { IBM_Plex_Sans_Arabic, Poppins } from "next/font/google";

import { BandeauFictif } from "@/components/BandeauFictif";

import "./globals.css";

// next/font télécharge les polices au moment du build et les sert depuis le site : aucun appel à Google côté visiteur.
const poppins = Poppins({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--police-poppins" });
const arabe = IBM_Plex_Sans_Arabic({ subsets: ["arabic"], weight: ["400", "500"], variable: "--police-arabe" });

export const metadata: Metadata = {
  title: "Wakil · Banque Atlas Démo",
  description: "Assistant bancaire qui comprend la darija. Données 100 % fictives – projet de démonstration.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="fr" className={`${poppins.variable} ${arabe.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col bg-fond font-sans text-texte">
        <BandeauFictif />
        {children}
      </body>
    </html>
  );
}
