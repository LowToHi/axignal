import type { Locale } from "./i18n";

export const tedBoundedProductProfile = {
  profileId: "ADMITTED_PUBLIC_SOURCE_PROFILE_01",
  sourceId: "PUBLIC_SOURCE_PROFILE_01",
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
    admitted: "A bounded public-source profile is admitted for the private authenticated pilot.",
    boundary: "Public access and unrestricted source use remain disabled.",
    synthetic: "Synthetic product demonstration"
  },
  es: {
    admitted: "Un perfil acotado de fuente pública está admitido para el piloto privado autenticado.",
    boundary: "El acceso público y el uso irrestricto de fuentes siguen desactivados.",
    synthetic: "Demostración sintética del producto"
  },
  fr: {
    admitted: "Un profil limité de source publique est admis pour le pilote privé authentifié.",
    boundary: "L’accès public et l’usage illimité des sources restent désactivés.",
    synthetic: "Démonstration produit synthétique"
  },
  pt: {
    admitted: "Um perfil limitado de fonte pública está admitido para o piloto privado autenticado.",
    boundary: "O acesso público e a utilização irrestrita de fontes continuam desativados.",
    synthetic: "Demonstração sintética do produto"
  },
  de: {
    admitted: "Ein begrenztes öffentliches Quellenprofil ist für den privaten authentifizierten Piloten zugelassen.",
    boundary: "Öffentlicher Zugang und uneingeschränkte Quellennutzung bleiben deaktiviert.",
    synthetic: "Synthetische Produktdemonstration"
  },
  it: {
    admitted: "Un profilo limitato di fonte pubblica è ammesso per il pilota privato autenticato.",
    boundary: "L’accesso pubblico e l’uso illimitato delle fonti restano disattivati.",
    synthetic: "Dimostrazione sintetica del prodotto"
  }
};
