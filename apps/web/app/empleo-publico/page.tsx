import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "AXIGNAL Public Employment",
  description:
    "Public Employment is an architectural draft. It is not launched, not indexable and not available for checkout.",
  robots: { index: false, follow: false, noarchive: true }
};

export default async function PublicEmploymentPage() {
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>Empleo Público — borrador arquitectónico</h1>
      <p>
        Esta superficie es una prueba arquitectónica del segundo shell de
        AXIGNAL. No está lanzada, no es indexable y no admite contratación.
      </p>
      <p>
        <em>
          Estado: DRAFT · No indexable · Sin checkout · Sin lanzamiento público.
        </em>
      </p>
      <p>
        <a href="/">← AXIGNAL</a>
      </p>
    </main>
  );
}
