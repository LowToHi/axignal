import type { PublicDiscoveryPage } from "@/lib/organic-server";

import styles from "../app/discovery-page.module.css";
import { TenderAlertForm } from "./tender-alert-form";

type Opportunity = {
  title: string;
  buyer: string;
  value_label: string;
  deadline: string;
  source_url?: string;
};

function text(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function opportunities(metrics: Record<string, unknown>): Opportunity[] {
  if (!Array.isArray(metrics.opportunities)) return [];
  return metrics.opportunities.flatMap((value) => {
    if (!value || typeof value !== "object") return [];
    const item = value as Record<string, unknown>;
    if (
      typeof item.title !== "string" ||
      typeof item.buyer !== "string"
    ) {
      return [];
    }
    return [
      {
        title: item.title,
        buyer: item.buyer,
        value_label: text(item.value_label, "Value not declared"),
        deadline: text(item.deadline, "Deadline not resolved"),
        ...(typeof item.source_url === "string"
          ? { source_url: item.source_url }
          : {})
      }
    ];
  });
}

function money(value: number, currency: string): string {
  if (value <= 0) return "Not fully declared";
  return new Intl.NumberFormat("en", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1
  }).format(value / 1_000_000);
}

export function DiscoveryView({ page }: { page: PublicDiscoveryPage }) {
  const countryName = text(
    page.metrics.country_name,
    page.country_slug.replaceAll("-", " ")
  );
  const sectorName = text(
    page.metrics.sector_name,
    page.sector_slug.replaceAll("-", " ")
  );
  const currency = text(page.metrics.currency, "EUR");
  const latest = opportunities(page.metrics);
  const siteUrl = (
    process.env.AXIGNAL_PUBLIC_SITE_URL ?? "https://axignal.com"
  ).replace(/\/$/, "");
  const canonicalUrl = `${siteUrl}${page.canonical_path}`;
  const testRuntime = process.env.AXIGNAL_TEST_RUNTIME_ENABLED === "true";
  const turnstileSiteKey =
    process.env.NEXT_PUBLIC_AXIGNAL_TURNSTILE_SITE_KEY;
  const datasetJsonLd = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: page.title,
    description: page.description,
    url: canonicalUrl,
    creator: {
      "@type": "Organization",
      name: "AXIGNAL",
      url: siteUrl
    },
    dateModified: page.freshness_at,
    temporalCoverage: `${page.published_at}/${page.expires_at}`,
    spatialCoverage: countryName,
    measurementTechnique: page.methodology_version,
    isAccessibleForFree: true,
    isBasedOn: page.source_urls,
    keywords: [
      countryName,
      sectorName,
      "public procurement",
      "B2G",
      "government tenders"
    ]
  };
  const pageJsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: page.title,
    description: page.description,
    url: canonicalUrl,
    dateModified: page.freshness_at,
    mainEntity: datasetJsonLd
  };

  return (
    <main className={styles.page}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(pageJsonLd) }}
      />
      <header className={styles.nav}>
        <a href="/" className={styles.brand}>
          AXIGNAL
        </a>
        <nav aria-label="Public intelligence">
          <a href="#opportunities">Opportunities</a>
          <a href="#market">Market</a>
          <a href="#methodology">Methodology</a>
        </nav>
        <a className={styles.productLink} href="/">
          Open workspace
        </a>
      </header>

      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <span>BUSINESS-TO-GOVERNMENT OPPORTUNITY INTELLIGENCE</span>
          <h1>{page.title}</h1>
          <p>{page.description}</p>
          <div className={styles.heroActions}>
            <a href="#opportunities">Explore opportunities</a>
            <a href="#alerts">Create alert</a>
          </div>
        </div>
        <div className={styles.snapshot}>
          <span>VERIFIABLE SNAPSHOT</span>
          <strong>v{page.snapshot_version}</strong>
          <dl>
            <div>
              <dt>Updated</dt>
              <dd>
                {new Date(page.freshness_at).toLocaleString("en-GB", {
                  dateStyle: "medium",
                  timeStyle: "short",
                  timeZone: "UTC"
                })}{" "}
                UTC
              </dd>
            </div>
            <div>
              <dt>Sources</dt>
              <dd>{page.source_count}</dd>
            </div>
            <div>
              <dt>Method</dt>
              <dd>{page.methodology_version}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className={styles.metrics} id="market">
        <article>
          <span>Active opportunities</span>
          <strong>
            {page.active_opportunity_count.toLocaleString("en")}
          </strong>
          <small>Admitted under the current freshness rule</small>
        </article>
        <article>
          <span>Public buyers</span>
          <strong>{page.unique_buyer_count.toLocaleString("en")}</strong>
          <small>Distinct resolved contracting authorities</small>
        </article>
        <article>
          <span>Known value</span>
          <strong>{money(page.known_value_microunits, currency)}</strong>
          <small>Undeclared values remain excluded</small>
        </article>
        <article>
          <span>Coverage</span>
          <strong>
            {text(page.metrics.coverage_label, "Declared sources")}
          </strong>
          <small>No claim of universal market coverage</small>
        </article>
      </section>

      <section className={styles.opportunitySection} id="opportunities">
        <div className={styles.sectionHeading}>
          <span>LATEST ADMITTED OPPORTUNITIES</span>
          <h2>
            Public contracts in {countryName} · {sectorName}
          </h2>
          <p>
            Each row preserves the buyer, deadline, value state and source
            link. Qualification and bid decisions remain inside the governed
            AXIGNAL workspace.
          </p>
        </div>
        <div className={styles.tableWrap}>
          <table>
            <thead>
              <tr>
                <th>Opportunity</th>
                <th>Buyer</th>
                <th>Value</th>
                <th>Deadline</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {latest.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    The current snapshot contains aggregate intelligence but
                    no public detail rows.
                  </td>
                </tr>
              ) : (
                latest.map((item) => (
                  <tr key={`${item.title}:${item.buyer}`}>
                    <td>
                      <strong>{item.title}</strong>
                    </td>
                    <td>{item.buyer}</td>
                    <td>{item.value_label}</td>
                    <td>{item.deadline}</td>
                    <td>
                      {item.source_url ? (
                        <a
                          href={item.source_url}
                          rel="nofollow noopener"
                        >
                          Official notice
                        </a>
                      ) : (
                        "Source retained"
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className={styles.alertSection} id="alerts">
        <TenderAlertForm
          countryCode={page.country_code}
          sectorSlug={page.sector_slug}
          sourcePath={page.canonical_path}
          testRuntime={testRuntime}
          {...(turnstileSiteKey ? { turnstileSiteKey } : {})}
        />
      </section>

      <section className={styles.methodology} id="methodology">
        <div>
          <span>METHODOLOGY & PROVENANCE</span>
          <h2>What this page can—and cannot—claim.</h2>
        </div>
        <div className={styles.methodCards}>
          <article>
            <b>Observed</b>
            <p>
              Counts and values derive from the source records admitted to
              snapshot {page.snapshot_version}.
            </p>
          </article>
          <article>
            <b>Unknown</b>
            <p>
              Missing values, incomplete jurisdictions and unavailable notices
              are not silently estimated.
            </p>
          </article>
          <article>
            <b>Freshness</b>
            <p>
              This snapshot expires at{" "}
              {new Date(page.expires_at).toLocaleString("en-GB", {
                dateStyle: "medium",
                timeStyle: "short",
                timeZone: "UTC"
              })}{" "}
              UTC unless superseded.
            </p>
          </article>
          <article>
            <b>Decision authority</b>
            <p>
              AXIGNAL can propose opportunity fit. A human retains bid,
              pricing, partnership and submission authority.
            </p>
          </article>
        </div>
        <details>
          <summary>Source basis</summary>
          <ul>
            {page.source_urls.map((url) => (
              <li key={url}>
                <a href={url} rel="nofollow noopener">
                  {url}
                </a>
              </li>
            ))}
          </ul>
        </details>
      </section>

      <footer className={styles.footer}>
        <span>AXIGNAL · Global B2G Opportunity Intelligence</span>
        <span>Dataset ≠ indexable page · Citation ≠ endorsement</span>
      </footer>
    </main>
  );
}
