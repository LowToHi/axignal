import type { Locale } from "./i18n";

export const tedBoundedProductProfile = {
  profileId: "TED_SEARCH_API_BOUNDED_PRODUCT_PROFILE",
  sourceId: "EU_TED",
  admissionState: "PRODUCT_ADMITTED",
  accessScope: "PRIVATE_AUTHENTICATED_PILOT",
  publicAccess: "PUBLIC_ACCESS_DISABLED",
  unrestrictedSourceUse: false,
  demonstrationData: "SYNTHETIC_FIXTURES"
} as const;

export const productProfileCopy: Record<
  Locale,
  {
    admitted: string;
    boundary: string;
    synthetic: string;
  }
> = {
  en: {
    admitted: "TED bounded product profile admitted for private authenticated pilot.",
    boundary: "Public access and unrestricted source use remain disabled.",
    synthetic: "Synthetic product demonstration"
  },
  es: {
    admitted: "El perfil acotado de TED está admitido para el piloto privado autenticado.",
    boundary: "El acceso público y el uso irrestricto de fuentes siguen desactivados.",
    synthetic: "Demostración sintética del producto"
  },
  fr: {
    admitted: "Le profil TED limité est admis pour le pilote privé authentifié.",
    boundary: "L’accès public et l’usage illimité des sources restent désactivés.",
    synthetic: "Démonstration produit synthétique"
  },
  pt: {
    admitted: "O perfil TED limitado está admitido para o piloto privado autenticado.",
    boundary: "O acesso público e a utilização irrestrita de fontes continuam desativados.",
    synthetic: "Demonstração sintética do produto"
  },
  de: {
    admitted: "Das begrenzte TED-Produktprofil ist für den privaten authentifizierten Piloten zugelassen.",
    boundary: "Öffentlicher Zugang und uneingeschränkte Quellennutzung bleiben deaktiviert.",
    synthetic: "Synthetische Produktdemonstration"
  },
  it: {
    admitted: "Il profilo TED limitato è ammesso per il pilota privato autenticato.",
    boundary: "L’accesso pubblico e l’uso illimitato delle fonti restano disattivati.",
    synthetic: "Dimostrazione sintetica del prodotto"
  }
};
