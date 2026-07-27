"use client";

import { FormEvent, useMemo, useState } from "react";

type Lens = "AUTO" | "GLOBE" | "GRAPH" | "DUAL";
type Theme = "dark" | "light";
type Message = { id: number; actor: "user" | "axignal"; text: string };

type Claim = {
  kind: "HECHO" | "INFERENCIA" | "PREDICCIÓN" | "CONTRADICCIÓN" | "DESCONOCIDO";
  text: string;
  source: string;
};

const opportunities = [
  { name: "Distrito de Ramenki", return: "18.7%", confidence: 4, level: "ALTA" },
  { name: "Zona ZIL", return: "16.2%", confidence: 4, level: "ALTA" },
  { name: "Khamovniki", return: "12.1%", confidence: 3, level: "MEDIA" },
  { name: "Basmanniy", return: "9.8%", confidence: 2, level: "MEDIA-BAJA" }
] as const;

const claims: Claim[] = [
  {
    kind: "HECHO",
    text: "Los precios de alquiler en Ramenki han crecido un 14% interanual.",
    source: "CBR Research · 15 Abr 2024"
  },
  {
    kind: "INFERENCIA",
    text: "La nueva línea de metro aumentaría la demanda en un 15–20%.",
    source: "Modelo de transporte · 03 Mar 2024"
  },
  {
    kind: "PREDICCIÓN",
    text: "Se espera escasez de oferta de vivienda premium en 2025.",
    source: "Modelo demográfico + oferta · 28 Feb 2024"
  },
  {
    kind: "CONTRADICCIÓN",
    text: "Altas tasas hipotecarias podrían reducir la demanda en 2025.",
    source: "Banco de Rusia · 10 May 2024"
  },
  {
    kind: "DESCONOCIDO",
    text: "No hay evidencia suficiente sobre futuros cambios fiscales.",
    source: "Cobertura incompleta"
  }
];

const initialMessages: Message[] = [
  { id: 1, actor: "user", text: "Quiero ver si hay oportunidades inmobiliarias en Moscú" },
  {
    id: 2,
    actor: "axignal",
    text: "He centrado la investigación en Moscú, Rusia, en oportunidades inmobiliarias para 12–24 meses."
  },
  {
    id: 3,
    actor: "axignal",
    text: "He identificado 12 oportunidades. Ramenki, ZIL y Khamovniki concentran el potencial inicial."
  }
];

function Confidence({ value }: { value: number }) {
  return (
    <span className="confidence" aria-label={`Confianza ${value} de 5`}>
      {Array.from({ length: 5 }, (_, index) => (
        <i key={index} data-on={index < value} />
      ))}
    </span>
  );
}

function GlobeSurface() {
  return (
    <div className="globe-stage" aria-label="Globe centrado en Moscú">
      <div className="star-field" />
      <div className="globe">
        <div className="globe-grid" />
        <span className="signal signal-moscow" />
        <span className="signal signal-europe" />
        <span className="signal signal-me" />
        <span className="signal signal-asia" />
        <div className="moscow-card">
          <strong>Moscú, Rusia</strong>
          <span>12 oportunidades detectadas</span>
          <span>Potencial promedio <b>ALTO</b></span>
          <span>Retorno esperado <b>18.7%</b></span>
        </div>
      </div>
      <div className="potential-legend">
        <span>POTENCIAL</span>
        <div className="legend-gradient" />
        <div className="legend-labels"><small>Muy bajo</small><small>Medio</small><small>Muy alto</small><small>Sin datos</small></div>
      </div>
    </div>
  );
}

function GraphSurface() {
  const nodes = [
    { id: "moscow", x: 50, y: 48, label: "Moscú" },
    { id: "ramenki", x: 25, y: 26, label: "Ramenki" },
    { id: "metro", x: 72, y: 24, label: "Metro" },
    { id: "demand", x: 78, y: 66, label: "Demanda" },
    { id: "rates", x: 28, y: 74, label: "Tipos" }
  ];

  return (
    <div className="graph-stage" aria-label="Grafo de relaciones de la oportunidad">
      <svg viewBox="0 0 100 100" role="img" aria-label="Relaciones causales de la investigación">
        <line x1="50" y1="48" x2="25" y2="26" className="edge support" />
        <line x1="50" y1="48" x2="72" y2="24" className="edge inferred" />
        <line x1="50" y1="48" x2="78" y2="66" className="edge support" />
        <line x1="50" y1="48" x2="28" y2="74" className="edge contradiction" />
        <line x1="72" y1="24" x2="78" y2="66" className="edge inferred" />
        {nodes.map((node) => (
          <g key={node.id} className={node.id === "moscow" ? "node selected" : "node"}>
            <circle cx={node.x} cy={node.y} r={node.id === "moscow" ? 8 : 6} />
            <text x={node.x} y={node.y + 1}>{node.label}</text>
          </g>
        ))}
      </svg>
      <div className="graph-caption">
        <strong>Transmission graph</strong>
        <span>Relaciones tipadas · contexto preservado</span>
      </div>
    </div>
  );
}

function PrimaryCanvas({ lens }: { lens: Lens }) {
  if (lens === "GRAPH") return <GraphSurface />;
  if (lens === "DUAL") {
    return (
      <div className="dual-stage">
        <GlobeSurface />
        <GraphSurface />
      </div>
    );
  }
  return <GlobeSurface />;
}

export function InvestigationShell() {
  const [lens, setLens] = useState<Lens>("GLOBE");
  const [theme, setTheme] = useState<Theme>("dark");
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [draft, setDraft] = useState("");
  const [selectedOpportunity, setSelectedOpportunity] = useState(0);
  const selected = opportunities[selectedOpportunity] ?? opportunities[0];

  const interpretedLens = useMemo(() => (lens === "AUTO" ? "GLOBE · intención geográfica" : lens), [lens]);

  function toggleTheme() {
    const nextTheme: Theme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;
  }

  function submitMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    const userMessage: Message = { id: Date.now(), actor: "user", text };
    const lower = text.toLocaleLowerCase("es");
    let response = "He conservado el contexto y he añadido la orden al Investigation Trail.";
    if (lower.includes("grafo") || lower.includes("graph")) {
      setLens("GRAPH");
      response = "He cambiado a Graph y conservado Moscú, la oportunidad, los claims, la evidencia y el periodo.";
    } else if (lower.includes("globo") || lower.includes("globe") || lower.includes("mapa")) {
      setLens("GLOBE");
      response = "He cambiado a Globe y mantenido el contexto de investigación.";
    } else if (lower.includes("contradic")) {
      response = "Hay una contradicción material: las tasas hipotecarias pueden reducir la demanda en 2025.";
    } else if (lower.includes("dual")) {
      setLens("DUAL");
      response = "He activado Dual para comparar geografía y relaciones simultáneamente.";
    }
    setMessages((current) => [...current, userMessage, { id: Date.now() + 1, actor: "axignal", text: response }]);
    setDraft("");
  }

  return (
    <main className="shell" data-current-theme={theme}>
      <header className="topbar">
        <a className="brand" href="#" aria-label="AXIGNAL home">AXIGNAL</a>
        <div className="context-path"><span>Moscú, Rusia</span><b>/</b><span>Real Estate</span><b>/</b><span>12–24 meses</span></div>
        <nav className="lens-switch" aria-label="Seleccionar lente">
          {(["AUTO", "GLOBE", "GRAPH", "DUAL"] as Lens[]).map((item) => (
            <button key={item} type="button" aria-pressed={lens === item} onClick={() => setLens(item)}>{item}</button>
          ))}
        </nav>
        <label className="search"><span>⌕</span><input aria-label="Buscar" placeholder="Buscar entidades, temas, fuentes…" /></label>
        <select aria-label="Idioma" defaultValue="es"><option value="en">EN</option><option value="es">ES</option><option value="fr">FR</option><option value="de">DE</option><option value="pt-BR">PT</option><option value="zh-Hans">中文</option></select>
        <button className="icon-button" type="button" onClick={toggleTheme} aria-label="Cambiar tema">{theme === "dark" ? "☾" : "☀"}</button>
      </header>

      <aside className="rail-nav" aria-label="Navegación primaria">
        <button aria-label="Inicio">⌂</button><button className="active" aria-label="Globe">◎</button><button aria-label="Graph">⌘</button><button aria-label="Oportunidades">◇</button><button aria-label="Claims">▱</button><button aria-label="Trails">↺</button>
        <span className="avatar">AN</span>
      </aside>

      <section className="navigator panel" aria-label="AXIGNAL Navigator">
        <div className="panel-title"><strong>AXIGNAL NAVIGATOR</strong><span className="online">● ONLINE</span></div>
        <div className="messages">
          {messages.map((message) => (
            <article key={message.id} className={`message ${message.actor}`}>
              <div><strong>{message.actor === "user" ? "TÚ" : "AXIGNAL"}</strong><time>10:2{message.id % 10}</time></div>
              <p>{message.text}</p>
              {message.actor === "axignal" && <button type="button">Ver interpretación</button>}
            </article>
          ))}
        </div>
        <div className="interpretation"><span>INTERPRETACIÓN ACTIVA</span><b>{interpretedLens}</b></div>
        <form className="composer" onSubmit={submitMessage}>
          <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Escribe una orden o pregunta…" aria-label="Mensaje para AXIGNAL" />
          <button type="submit" aria-label="Enviar">➤</button>
        </form>
      </section>

      <section className="workspace panel">
        <div className="canvas-toolbar"><strong>{lens === "AUTO" ? "AUTO · GLOBE" : lens} VIEW</strong><span>Moscú · contexto sincronizado</span><button type="button">Filtros</button></div>
        <PrimaryCanvas lens={lens} />
        <div className="timeline" aria-label="Timeline de investigación">
          <button type="button" aria-label="Reproducir">▶</button><select aria-label="Horizonte"><option>12M</option><option>24M</option><option>36M</option></select>
          <div className="timeline-track"><i /><i /><i className="selected" /><i /><i /></div><span>HOY</span>
        </div>
        <div className="metrics">
          <article><span>OPORTUNIDADES</span><strong>12</strong><small>↑ 20% vs. periodo anterior</small></article>
          <article><span>POTENCIAL PROMEDIO</span><strong>18.7%</strong><small>Retorno esperado</small></article>
          <article><span>CONFIANZA PROMEDIO</span><strong>72%</strong><small>Media-alta</small></article>
          <article><span>SEÑALES DETECTADAS</span><strong>328</strong><small>↑ 15%</small></article>
          <article><span>FUENTES ANALIZADAS</span><strong>142</strong><small>↑ 12%</small></article>
        </div>
      </section>

      <aside className="right-column">
        <section className="opportunities panel">
          <div className="panel-title"><strong>OPORTUNIDADES (12)</strong><span>Ordenar: Potencial</span></div>
          {opportunities.map((opportunity, index) => (
            <button className="opportunity" data-selected={index === selectedOpportunity} key={opportunity.name} type="button" onClick={() => setSelectedOpportunity(index)}>
              <span><strong>{opportunity.name}</strong><em>{opportunity.level}</em></span>
              <span>Retorno esperado <b>{opportunity.return}</b></span>
              <span>Confianza <Confidence value={opportunity.confidence} /></span>
            </button>
          ))}
        </section>
        <section className="claims panel">
          <div className="panel-title"><strong>CLAIM &amp; EVIDENCE RAIL</strong><span>{selected.name}</span></div>
          <div className="claim-tabs"><button className="active">Todos</button><button>Hechos</button><button>Inferencias</button><button>Predicciones</button></div>
          {claims.map((claim) => (
            <article className="claim" data-kind={claim.kind} key={claim.kind}>
              <span className="claim-kind">{claim.kind}</span><p>{claim.text}</p><small>{claim.source}</small><button type="button">VER</button>
            </article>
          ))}
          <button className="view-all" type="button">Ver evidencia completa →</button>
        </section>
      </aside>
    </main>
  );
}
