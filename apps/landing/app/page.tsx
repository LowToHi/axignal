const features = [
  ["Navigator", "Ask in natural language and make AXIGNAL move through the investigation with you."],
  ["Globe + Graph", "Move from geographic discovery to causal and ownership relationships without losing context."],
  ["Claims + Evidence", "Inspect support, contradiction, freshness, coverage and original sources before acting."],
  ["Timeline", "Reconstruct what was known at a point in time and monitor how an opportunity changes."],
  ["Knowledge Tides", "See where qualified attention is accelerating without confusing interest with market truth."],
  ["Investigation Trails", "Save, resume and share a complete, auditable research path."]
] as const;

const plans = [
  {
    name: "Research",
    audience: "Independent professionals",
    price: "Early access",
    cta: "Request access",
    featured: false,
    features: ["Navigator", "Globe, Graph and Timeline", "Claims and evidence", "Saved investigations", "Core exports"]
  },
  {
    name: "Professional",
    audience: "Analysts and small teams",
    price: "Request pricing",
    cta: "Book a product session",
    featured: true,
    features: ["Everything in Research", "Team collaboration", "Advanced comparisons", "Extended history and alerts", "Professional exports"]
  },
  {
    name: "Enterprise",
    audience: "Organisations and intelligence teams",
    price: "Custom",
    cta: "Talk to AXIGNAL",
    featured: false,
    features: ["Everything in Professional", "SSO and audit controls", "Private sources and claims", "API and custom limits", "SLA and data controls"]
  }
] as const;

const faqs = [
  ["Is AXIGNAL a financial chatbot?", "No. Navigator controls a persistent investigation system composed of Globe, Graph, Timeline, claims and evidence."],
  ["Does AXIGNAL recommend investments?", "The initial product supports observation, research and comparison. It does not provide personalised investment advice or execute trades."],
  ["Where does the information come from?", "From admitted sources with explicit provenance, freshness, coverage, transformation history and usage rights."],
  ["Can I switch between Globe and Graph?", "Yes. AXIGNAL preserves the selected opportunity, claims, evidence, filters, time and conversation when the lens changes."],
  ["Which languages are planned?", "English by default, plus Spanish, French, German, Brazilian Portuguese and Simplified Chinese."],
  ["Are my searches visible to other customers?", "No individual research is exposed. Any future aggregate Knowledge Tide feature must use privacy thresholds, unique-user cohorts and explicit controls."],
  ["Is there an API?", "API access is part of the Professional or Enterprise packaging hypothesis and will only be advertised when available."],
  ["Can I cancel or change plan?", "Commercial terms will be displayed transparently before paid access. No hidden limits, fake discounts or surprise overages are permitted."]
] as const;

export default function LandingPage() {
  return (
    <main>
      <header className="site-header">
        <a className="wordmark" href="#top">AXIGNAL</a>
        <nav aria-label="Primary navigation">
          <a href="#product">Product</a>
          <a href="#use-cases">Use cases</a>
          <a href="#methodology">Methodology</a>
          <a href="#pricing">Pricing</a>
          <a href="#faq">FAQ</a>
        </nav>
        <div className="header-actions"><a href="/app">Sign in</a><a className="button small" href="#access">Request access</a></div>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <span className="eyebrow">GLOBAL OPPORTUNITY INTELLIGENCE</span>
          <h1>Discover global opportunities before they become obvious.</h1>
          <p>Navigate markets through Globe, Graph, Timeline, claims and verifiable evidence—inside one persistent investigation context.</p>
          <div className="hero-actions"><a className="button" href="#access">Request access</a><a className="button secondary" href="#demo">Explore the product</a></div>
          <div className="proof-line"><span>Traceable claims</span><span>Contradictions visible</span><span>Six-language architecture</span><span>No execution or custody</span></div>
        </div>
        <div className="hero-product" aria-label="AXIGNAL product preview">
          <div className="preview-top"><b>AXIGNAL</b><span>AUTO</span><span className="active">GLOBE</span><span>GRAPH</span><span>DUAL</span></div>
          <div className="preview-grid">
            <aside><strong>NAVIGATOR</strong><p>Show me real-estate opportunities in Moscow.</p><p className="assistant">I found 12 opportunities and preserved claims, evidence and time.</p></aside>
            <div className="preview-globe"><i /><b>Moscow</b><span>12 opportunities</span></div>
            <div className="preview-rail"><strong>CLAIMS &amp; EVIDENCE</strong><p data-kind="fact">FACT · Rental prices +14%</p><p data-kind="inference">INFERENCE · Metro demand effect</p><p data-kind="contradiction">CONTRADICTION · Rate pressure</p></div>
          </div>
        </div>
      </section>

      <section className="trust-strip"><span>Built for auditable research</span><span>Original sources preserved</span><span>Unknown coverage stays visible</span><span>Interest never becomes truth automatically</span></section>

      <section className="section demo" id="demo">
        <div className="section-heading"><span className="eyebrow">THE COMPLETE LOOP</span><h2>Ask. Explore. Verify. Compare. Track.</h2><p>AXIGNAL turns a natural-language question into a navigable, evidence-backed investigation rather than a one-off generated answer.</p></div>
        <ol className="flow"><li><b>01</b><span>Ask</span></li><li><b>02</b><span>Navigate</span></li><li><b>03</b><span>Discover</span></li><li><b>04</b><span>Verify</span></li><li><b>05</b><span>Compare</span></li><li><b>06</b><span>Track</span></li></ol>
      </section>

      <section className="section" id="product">
        <div className="section-heading"><span className="eyebrow">ONE INSTRUMENT</span><h2>Not a collection of disconnected dashboards.</h2></div>
        <div className="feature-grid">{features.map(([title, text]) => <article key={title}><span>◇</span><h3>{title}</h3><p>{text}</p></article>)}</div>
      </section>

      <section className="section split" id="use-cases">
        <div><span className="eyebrow">BUILT FOR HIGH-COST DECISIONS</span><h2>Recognise the opportunity. Then interrogate it.</h2><p>For investors, analysts, family offices, corporate strategy teams, advisers and intelligence operators researching across markets, assets and jurisdictions.</p></div>
        <ul><li>Global market discovery</li><li>Real assets and geographic comparison</li><li>Supply-chain and ownership exposure</li><li>Regulatory transmission</li><li>Cross-market scenario research</li><li>Opportunity monitoring and audit trails</li></ul>
      </section>

      <section className="section methodology" id="methodology">
        <div className="section-heading"><span className="eyebrow">TRUST BY CONSTRUCTION</span><h2>Every conclusion should expose what supports it—and what could invalidate it.</h2></div>
        <div className="method-grid"><article><b>Observed</b><p>Directly represented from admitted source evidence.</p></article><article><b>Calculated</b><p>Reproducible transformations with versioned methods.</p></article><article><b>Inferred</b><p>Explicit reasoning separated from source observation.</p></article><article><b>Predicted</b><p>Forward-looking claims with scenarios and uncertainty.</p></article><article><b>Contradicted</b><p>Material counter-evidence remains visible.</p></article><article><b>Unknown</b><p>Missing coverage is never rendered as a weak value.</p></article></div>
        <a className="text-link" href="/methodology">Read the public methodology →</a>
      </section>

      <section className="section pricing" id="pricing">
        <div className="section-heading"><span className="eyebrow">PACKAGING UNDER VALIDATION</span><h2>Choose the research depth your decisions require.</h2><p>Plan names, prices and limits remain hypotheses until willingness-to-pay, cost and margin gates pass. Early access will never use fake discounts or hidden overages.</p></div>
        <div className="plan-grid">{plans.map((plan) => <article className={plan.featured ? "plan featured" : "plan"} key={plan.name}>{plan.featured && <span className="plan-label">Candidate professional fit</span>}<h3>{plan.name}</h3><p>{plan.audience}</p><strong>{plan.price}</strong><ul>{plan.features.map((feature) => <li key={feature}>✓ {feature}</li>)}</ul><a className={plan.featured ? "button" : "button secondary"} href="#access">{plan.cta}</a></article>)}</div>
        <div className="comparison"><h3>Plan comparison</h3><div><span>Navigator, Globe, Graph and Timeline</span><b>All plans</b></div><div><span>Claims, evidence and saved trails</span><b>All plans</b></div><div><span>Team collaboration and advanced comparison</span><b>Professional+</b></div><div><span>Private sources, API, SSO and audit controls</span><b>Enterprise</b></div></div>
      </section>

      <section className="section trust" id="trust"><div><span className="eyebrow">SECURITY, PRIVACY AND SOURCE RIGHTS</span><h2>Your investigation is not a public signal.</h2><p>Private research, personalisation and aggregate Knowledge Tides are separate purposes with separate controls. Enterprise controls, source rights, retention and exports are documented in the Trust Center.</p><a className="text-link" href="/trust">Visit the Trust Center →</a></div><div className="trust-card"><span>Tenant isolation</span><span>Purpose-specific controls</span><span>Source-right enforcement</span><span>Auditable claims</span><span>Export restrictions</span><span>Incident and rollback runbooks</span></div></section>

      <section className="section faq" id="faq"><div className="section-heading"><span className="eyebrow">FREQUENTLY ASKED QUESTIONS</span><h2>Understand the product before requesting access.</h2></div><div className="faq-list">{faqs.map(([question, answer]) => <details key={question}><summary>{question}</summary><p>{answer}</p></details>)}</div></section>

      <section className="final-cta" id="access"><span className="eyebrow">EARLY ACCESS</span><h2>See the world before the market does.</h2><p>Request an AXIGNAL product session and help validate the next generation of global opportunity research.</p><form><label><span>Work email</span><input type="email" name="email" placeholder="you@company.com" required /></label><label><span>Role</span><select name="role" defaultValue=""><option value="" disabled>Select your role</option><option>Investor</option><option>Analyst</option><option>Family office</option><option>Corporate strategy</option><option>Adviser</option><option>Other</option></select></label><button className="button" type="submit">Request access</button></form><small>Submitting this form does not create a paid subscription. Commercial terms will be shown before purchase.</small></section>

      <footer><a className="wordmark" href="#top">AXIGNAL</a><div><a href="#product">Product</a><a href="#pricing">Pricing</a><a href="/methodology">Methodology</a><a href="/trust">Trust Center</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="/accessibility">Accessibility</a></div><span>© 2026 AXIGNAL · axignal.com</span></footer>
    </main>
  );
}
