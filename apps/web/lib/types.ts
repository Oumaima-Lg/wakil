// Ce que renvoie GET /moi/espace (agent-api). Les montants arrivent en texte exact (« 2350.00 »), jamais en float.
export type Profil = { id: number; civilite: "madame" | "monsieur"; prenom: string; nom: string; ville: string };
export type Compte = { id: number; rib_masque: string; plafond_virement: string; solde: string };
export type Operation = { id: number; date: string; montant: string; libelle: string };
export type Facture = { id: number; fournisseur: string; montant: string; statut: "payee" | "impayee" };
export type Beneficiaire = { id: number; nom: string; rib_masque: string; interne: boolean };

export type Espace = {
  profil: Profil;
  compte: Compte;
  operations: Operation[];
  factures: Facture[];
  beneficiaires: Beneficiaire[];
};
