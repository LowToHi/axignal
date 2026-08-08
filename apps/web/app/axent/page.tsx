import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "AXENT — Asistente de AXIGNAL",
  description:
    "Inteligencia conversacional, gestión operativa, onboarding y soporte.",
  robots: { index: false, follow: false },
};

/**
 * AXENT dedicated surface. The conversational panel is rendered by the
 * global assistant (layout); this page explains the assistant and its
 * governed boundaries.
 */
export default async function AxentPage() {
  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: 40 }}>
      <h1>AXENT</h1>
      <p>
        Inteligencia conversacional de AXIGNAL: consulta de oportunidades,
        gestión de pursuits y workspaces, onboarding y soporte. El panel
        flotante está disponible desde cualquier punto del producto.
      </p>
      <h2>Qué puede hacer</h2>
      <ul>
        <li>Buscar oportunidades en lenguaje natural con evidencia admitida.</li>
        <li>Explicar por qué una oportunidad encaja, con citas y cobertura.</li>
        <li>Consultar pursuits, workspaces, tareas y cambios recientes.</li>
        <li>Crear pursuits y tareas con confirmación explícita.</li>
        <li>Crear casos de soporte y escalar a humanos cuando hace falta.</li>
      </ul>
      <h2>Límites</h2>
      <ul>
        <li>No presenta ofertas ni garantiza adjudicaciones.</li>
        <li>No sustituye los portales oficiales.</li>
        <li>Las acciones materiales requieren confirmación y quedan auditadas.</li>
      </ul>
    </main>
  );
}
