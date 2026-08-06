"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { trackLandingEvent } from "@/lib/analytics";
import {
  localeLabels,
  localePath,
  locales,
  type LandingMessages,
  type Locale
} from "@/lib/i18n";
import { pricingCopy, pricingRowKeys } from "@/lib/pricing-data";
import { productProfileCopy, tedBoundedProductProfile } from "@/lib/product-profile";
import { ImpactCalculator } from "./impact-calculator";
import { PilotAccessForm } from "./pilot-access-form";
import { SemanticGlobe } from "./semantic-globe";

type LandingExperienceProps = {
  locale: Locale;
  messages: LandingMessages;
};

type CtaOrigin = "header" | "hero" | "pricing" | "footer";
type LandingTheme = "dark" | "light";

const themeLabels: Record<Locale, { dark: string; light: string; switchTo: string }> = {
  en: { dark: "Dark", light: "Light", switchTo: "Switch to" },
  es: { dark: "Oscuro", light: "Claro", switchTo: "Cambiar a tema" },
  fr: { dark: "Sombre", light: "Clair", switchTo: "Passer au thème" },
  pt: { dark: "Escuro", light: "Claro", switchTo: "Mudar para tema" },
  de: { dark: "Dunkel", light: "Hell", switchTo: "Zu Design wechseln" },
  it: { dark: "Scuro", light: "Chiaro", switchTo: "Passa al tema" }
};

const sceneIds = [
  "SCENE_GLOBAL",
  "SCENE_EUROPE",
  "SCENE_FRAGMENTATION",
  "SCENE_EVIDENCE",
  "SCENE_INVESTIGATION",
  "SCENE_DOSSIER"
] as const;

const traceObjects = [
  ["PORTAL", "Official portal", "source"],
  ["NOTICE", "Published notice", "record"],
  ["DOCUMENT", "Tender document", "record"],
  ["UPDATE", "Material update", "record"],
  ["EVIDENCE", "Evidence Object", "evidence"],
  ["CANDIDATE", "Candidate Claim", "candidate"],
  ["ADMITTED", "Admitted Claim", "admitted"],
  ["UNKNOWN", "Unresolved gap", "unknown"]
] as const;

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return reduced;
}

function LanguageMenu({ locale, label }: { locale: Locale; label: string }) {
  return (
    <details className="language-menu">
      <summary aria-label={label}>
        {locale.toUpperCase()}
        <span aria-hidden="true">⌄</span>
      </summary>
      <div>
        {locales.map((option) => (
          <a
            href={localePath(option)}
            hrefLang={option}
            aria-current={option === locale ? "page" : undefined}
            key={option}
            onClick={() => trackLandingEvent("language_change", { locale: option })}
          >
            {localeLabels[option]}
          </a>
        ))}
      </div>
    </details>
  );
}

function ThemeToggle({
  locale,
  theme,
  onToggle
}: {
  locale: Locale;
  theme: LandingTheme;
  onToggle: () => void;
}) {
  const labels = themeLabels[locale];
  const nextTheme = theme === "dark" ? "light" : "dark";

  return (
    <button
      className="theme-toggle"
      type="button"
      aria-label={`${labels.switchTo} ${labels[nextTheme].toLowerCase()}`}
      aria-pressed={theme === "light"}
      onClick={onToggle}
    >
      <span aria-hidden="true">{labels[theme]}</span>
      <span className="theme-toggle-indicator" aria-hidden="true" />
    </button>
  );
}

export function LandingExperience({ locale, messages: m }: LandingExperienceProps) {
  const root = useRef<HTMLDivElement>(null);
  const cinematic = useRef<HTMLElement>(null);
  const cinematicStage = useRef<HTMLDivElement>(null);
  const cinematicProgress = useRef(0);
  const trackedScene = useRef(-1);
  const [activeScene, setActiveScene] = useState(0);
  const [selectedPlan, setSelectedPlan] = useState("Design Partner");
  const [theme, setTheme] = useState<LandingTheme>("dark");
  const reducedMotion = useReducedMotion();
  const profileCopy = productProfileCopy[locale];
  const plans = pricingCopy[locale];

  useEffect(() => {
    trackLandingEvent("landing_view", { locale, landing_variant: "b2g_v1" });
  }, [locale]);

  useEffect(() => {
    const stored = window.localStorage.getItem("axignal-theme");
    if (stored === "light" || stored === "dark") {
      setTheme(stored);
      document.documentElement.dataset.theme = stored;
    }
  }, []);

  const toggleTheme = () => {
    setTheme((current) => {
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      window.localStorage.setItem("axignal-theme", next);
      return next;
    });
  };

  useEffect(() => {
    if (!root.current || !cinematic.current || !cinematicStage.current) return;

    gsap.registerPlugin(ScrollTrigger);
    const media = gsap.matchMedia();
    const context = gsap.context(() => {
      gsap.set("[data-section-reveal]", { autoAlpha: 1 });

      const buildCinematic = (endDistance: string, compact: boolean) => {
        const sceneElements = gsap.utils.toArray<HTMLElement>("[data-cinematic-scene]");
        const traceElements = gsap.utils.toArray<HTMLElement>(".trace-object");
        const graph = root.current?.querySelector<HTMLElement>(".investigation-graph");
        const dossier = root.current?.querySelector<HTMLElement>(".cinematic-dossier");
        const investigationFrame =
          root.current?.querySelector<HTMLElement>(".investigation-context-frame");
        const driver = { value: 0 };
        const positionScale = compact ? 0.5 : 1;

        const fragmentationPositions = ([
          [-390, -185],
          [-155, -255],
          [85, -205],
          [315, -115],
          [-330, 80],
          [-75, 185],
          [205, 130],
          [385, 220]
        ] satisfies Array<[number, number]>).map(
          ([x, y]) => [x * positionScale, y * positionScale] as [number, number]
        );
        const evidencePositions = ([
          [-350, -105],
          [-350, 5],
          [-350, 115],
          [-95, -105],
          [-95, 5],
          [170, -105],
          [170, 5],
          [170, 115]
        ] satisfies Array<[number, number]>).map(
          ([x, y]) => [x * positionScale, y * positionScale] as [number, number]
        );
        const graphPositions = ([
          [-420, -160],
          [-250, -210],
          [-80, -160],
          [-330, 35],
          [-120, 10],
          [-140, -55],
          [-100, 150],
          [-220, 205]
        ] satisfies Array<[number, number]>).map(
          ([x, y]) => [x * positionScale, y * positionScale] as [number, number]
        );

        gsap.set(sceneElements, { autoAlpha: 0, y: 28 });
        gsap.set('[data-cinematic-scene="global"]', { autoAlpha: 1, y: 0 });
        gsap.set(traceElements, { autoAlpha: 0, scale: 0.35, x: 0, y: 0 });
        gsap.set([graph, dossier, investigationFrame], { autoAlpha: 0 });

        const timeline = gsap.timeline({
          id: "investigationCinematic",
          defaults: { ease: "none" },
          scrollTrigger: {
            trigger: cinematic.current,
            start: "top top",
            end: endDistance,
            pin: cinematicStage.current,
            scrub: compact ? 0.65 : 1,
            anticipatePin: 1,
            invalidateOnRefresh: true
          }
        });

        timeline
          .addLabel("SCENE_GLOBAL", 0)
          .to(
            driver,
            {
              value: 1,
              duration: 6,
              onUpdate: () => {
                cinematicProgress.current = driver.value;
                const nextScene = Math.min(5, Math.floor(driver.value * 6));
                if (nextScene !== trackedScene.current) {
                  trackedScene.current = nextScene;
                  setActiveScene(nextScene);
                  trackLandingEvent("demo_chapter_view", {
                    locale,
                    chapter: nextScene + 1
                  });
                }
              }
            },
            0
          )
          .to('[data-cinematic-scene="global"]', { autoAlpha: 0, x: -60, duration: 0.52 }, 0.56)
          .fromTo(
            '[data-cinematic-scene="europe"]',
            { autoAlpha: 0, x: 68, y: 0 },
            { autoAlpha: 1, x: 0, duration: 0.68 },
            0.66
          )
          .addLabel("SCENE_EUROPE", 1)
          .to('[data-cinematic-scene="europe"]', { autoAlpha: 0, x: -52, duration: 0.5 }, 1.62)
          .fromTo(
            '[data-cinematic-scene="fragmentation"]',
            { autoAlpha: 0, y: 34 },
            { autoAlpha: 1, y: 0, duration: 0.55 },
            1.72
          )
          .to(
            [".cinematic-profile", ".globe-selected"],
            { autoAlpha: 0, duration: 0.38 },
            1.55
          )
          .to(
            traceElements,
            {
              autoAlpha: 1,
              scale: 1,
              x: (index) => fragmentationPositions[index]?.[0] ?? 0,
              y: (index) => fragmentationPositions[index]?.[1] ?? 0,
              duration: 0.72,
              stagger: 0.035
            },
            1.76
          )
          .addLabel("SCENE_FRAGMENTATION", 2)
          .to('[data-cinematic-scene="fragmentation"]', { autoAlpha: 0, y: -24, duration: 0.46 }, 2.58)
          .fromTo(
            '[data-cinematic-scene="evidence"]',
            { autoAlpha: 0, y: 30 },
            { autoAlpha: 1, y: 0, duration: 0.52 },
            2.67
          )
          .to(
            traceElements,
            {
              x: (index) => evidencePositions[index]?.[0] ?? 0,
              y: (index) => evidencePositions[index]?.[1] ?? 0,
              scale: (index) => (index < 4 ? 0.72 : 1),
              duration: 0.78,
              stagger: 0.025
            },
            2.7
          )
          .addLabel("SCENE_EVIDENCE", 3)
          .to('[data-cinematic-scene="evidence"]', { autoAlpha: 0, x: -42, duration: 0.46 }, 3.55)
          .fromTo(
            '[data-cinematic-scene="investigation"]',
            { autoAlpha: 0, x: 54, y: 0 },
            { autoAlpha: 1, x: 0, duration: 0.55 },
            3.62
          )
          .to([graph, investigationFrame], { autoAlpha: 1, duration: 0.48 }, 3.65)
          .to(
            traceElements,
            {
              x: (index) => graphPositions[index]?.[0] ?? 0,
              y: (index) => graphPositions[index]?.[1] ?? 0,
              scale: 0.78,
              duration: 0.82,
              stagger: 0.018
            },
            3.72
          )
          .addLabel("SCENE_INVESTIGATION", 4)
          .to(
            ['[data-cinematic-scene="investigation"]', graph, investigationFrame],
            { autoAlpha: 0, duration: 0.44 },
            4.54
          )
          .to(
            traceElements,
            {
              x: compact ? -82 : -270,
              y: (index) => (index - 3.5) * (compact ? 18 : 26),
              scale: 0.48,
              autoAlpha: 0.42,
              duration: 0.7,
              stagger: 0.015
            },
            4.62
          )
          .fromTo(
            ".cinematic-dossier",
            { autoAlpha: 0, scale: 0.93, x: 45 },
            { autoAlpha: 1, scale: 1, x: 0, duration: 0.72 },
            4.74
          )
          .addLabel("SCENE_DOSSIER", 5)
          .to(".cinematic-pricing-cue", { autoAlpha: 1, y: 0, duration: 0.4 }, 5.48)
          .to(
            [dossier, traceElements],
            { autoAlpha: 0, y: -28, duration: 0.45 },
            5.73
          );

        return () => timeline.kill();
      };

      media.add("(prefers-reduced-motion: no-preference) and (min-width: 901px)", () =>
        buildCinematic("+=560%", false)
      );
      media.add(
        "(prefers-reduced-motion: no-preference) and (min-width: 641px) and (max-width: 900px)",
        () => buildCinematic("+=430%", true)
      );
      media.add("(prefers-reduced-motion: no-preference) and (max-width: 640px)", () =>
        buildCinematic("+=340%", true)
      );
      media.add("(prefers-reduced-motion: reduce)", () => {
        cinematicProgress.current = 0.2;
        gsap.set('[data-cinematic-scene="global"]', { autoAlpha: 1 });
        gsap.set(
          [
            '[data-cinematic-scene="europe"]',
            '[data-cinematic-scene="fragmentation"]',
            '[data-cinematic-scene="evidence"]',
            '[data-cinematic-scene="investigation"]',
            '[data-cinematic-scene="dossier"]',
            ".trace-system",
            ".investigation-graph",
            ".investigation-context-frame",
            ".cinematic-dossier"
          ],
          { display: "none" }
        );
      });

      media.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.utils.toArray<HTMLElement>("[data-section-reveal]").forEach((section) => {
          gsap.from(section, {
            id: "sectionReveal",
            y: 30,
            autoAlpha: 0,
            duration: 0.72,
            ease: "power3.out",
            scrollTrigger: { trigger: section, start: "top 86%", once: true }
          });
        });
      });
    }, root);

    return () => {
      media.revert();
      context.revert();
    };
  }, [locale]);

  useEffect(() => {
    const rootElement = root.current;
    if (!rootElement) return;

    let firstFrame = 0;
    let secondFrame = 0;

    const alignTarget = (target: HTMLElement) => {
      const headerOffset = target.id === "product" ? 0 : 76;
      const previousScrollBehavior = document.documentElement.style.scrollBehavior;
      document.documentElement.style.scrollBehavior = "auto";
      window.scrollTo({
        top: window.scrollY + target.getBoundingClientRect().top - headerOffset,
        behavior: "auto"
      });
      document.documentElement.style.scrollBehavior = previousScrollBehavior;
    };

    const settleTarget = (target: HTMLElement) => {
      alignTarget(target);
      firstFrame = window.requestAnimationFrame(() => {
        secondFrame = window.requestAnimationFrame(() => alignTarget(target));
      });
    };

    const handleAnchorClick = (event: MouseEvent) => {
      const origin = event.target;
      if (!(origin instanceof Element)) return;
      const anchor = origin.closest<HTMLAnchorElement>('a[href^="#"]');
      const href = anchor?.getAttribute("href");
      if (!href || href === "#") return;
      const target = document.getElementById(href.slice(1));
      if (!target) return;
      event.preventDefault();
      window.history.pushState(null, "", href);
      settleTarget(target);
    };

    rootElement.addEventListener("click", handleAnchorClick);

    const initialHash = window.location.hash.slice(1);
    const initialTarget = initialHash ? document.getElementById(initialHash) : null;
    if (initialTarget) settleTarget(initialTarget);

    return () => {
      rootElement.removeEventListener("click", handleAnchorClick);
      window.cancelAnimationFrame(firstFrame);
      window.cancelAnimationFrame(secondFrame);
    };
  }, []);

  const handleCta = (origin: CtaOrigin) => {
    trackLandingEvent("cta_click", { locale, cta_origin: origin, landing_variant: "b2g_v1" });
  };

  const selectPlan = (plan: string) => {
    setSelectedPlan(plan);
    trackLandingEvent("pricing_plan_select", { locale, plan });
    handleCta("pricing");
  };

  return (
    <div
      ref={root}
      className={`landing-root${reducedMotion ? " is-reduced-motion" : ""}`}
    >
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <header className="site-header">
        <a className="brand-lockup" href={localePath(locale)} aria-label="AXIGNAL home">
          <Image
            className="brand-logo brand-logo-dark"
            src="/brand/axignal-logo-dark.svg"
            alt="AXIGNAL"
            width={1895}
            height={406}
            priority
          />
          <Image
            className="brand-logo brand-logo-light"
            src="/brand/axignal-logo.svg"
            alt=""
            width={1895}
            height={406}
            aria-hidden="true"
          />
        </a>
        <nav aria-label="Primary navigation">
          <a href="#product">{m.nav.product}</a>
          <a href="#method">{m.nav.method}</a>
          <a href="#pricing">{m.nav.pricing}</a>
          <a href="#faq">{m.nav.faq}</a>
        </nav>
        <div className="header-actions">
          <ThemeToggle locale={locale} theme={theme} onToggle={toggleTheme} />
          <LanguageMenu locale={locale} label={m.nav.language} />
          <a className="button button-small" href="#access" onClick={() => handleCta("header")}>
            {m.nav.cta}
          </a>
        </div>
      </header>

      <main id="main-content">
        <section className="cinematic-shell" id="product" ref={cinematic}>
          <div className="cinematic-stage" ref={cinematicStage}>
            <SemanticGlobe
              progressRef={cinematicProgress}
              reducedMotion={reducedMotion}
              lightTheme={theme === "light"}
              locale={locale}
              labels={m.globe}
            />

            <div className="cinematic-grid" aria-hidden="true" />
            <div className="cinematic-running-head">
              <span>AXIGNAL / INVESTIGATION_CONTEXT</span>
              <span>{String(activeScene + 1).padStart(2, "0")} / 06</span>
            </div>

            <article className="cinematic-scene scene-global" data-cinematic-scene="global">
              <p className="eyebrow">{m.hero.eyebrow}</p>
              <h1>
                <span>{m.hero.title}</span>
                <span>{m.hero.accent}</span>
              </h1>
              <p className="scene-descriptor">{m.hero.descriptor}</p>
              <p>{m.hero.summary}</p>
              <div className="hero-actions">
                <a className="button" href="#access" onClick={() => handleCta("hero")}>
                  {m.hero.primary}
                </a>
                <a className="button button-ghost" href="#cinematic-progress">
                  {m.hero.secondary}
                </a>
              </div>
              <div className="hero-proof">
                {m.hero.proof.map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </div>
            </article>

            <article className="cinematic-scene scene-europe" data-cinematic-scene="europe">
              <p className="eyebrow">SCENE 02 · EUROPE</p>
              <h2>{m.acts[2]?.title}</h2>
              <p>{m.acts[2]?.body}</p>
              <div className="navigator-query">
                <span>{m.navigator.label}</span>
                <p>{m.navigator.prompt}</p>
                <ul>
                  {m.navigator.context.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </article>

            <article
              className="cinematic-scene scene-fragmentation"
              data-cinematic-scene="fragmentation"
            >
              <p className="eyebrow">SCENE 03 · PUBLIC RECORD</p>
              <h2>{m.acts[0]?.title}</h2>
              <p>{m.acts[0]?.body}</p>
              <small>Portal ≠ notice ≠ document ≠ update</small>
            </article>

            <article className="cinematic-scene scene-evidence" data-cinematic-scene="evidence">
              <p className="eyebrow">SCENE 04 · EPISTEMIC PIPELINE</p>
              <h2>{m.acts[4]?.title}</h2>
              <p>{m.acts[5]?.body}</p>
              <div className="evidence-state-rail" aria-label="Admission sequence">
                {m.evidence.pipeline.map((step, index) => (
                  <span key={step}>
                    {String(index + 1).padStart(2, "0")} · {step}
                  </span>
                ))}
              </div>
            </article>

            <article
              className="cinematic-scene scene-investigation"
              data-cinematic-scene="investigation"
            >
              <p className="eyebrow">SCENE 05 · INVESTIGATION_CONTEXT</p>
              <h2>{m.acts[6]?.title}</h2>
              <p>{m.navigator.response}</p>
            </article>

            <div className="trace-system" aria-hidden="true">
              {traceObjects.map(([state, label, kind]) => (
                <div className="trace-object" data-kind={kind} data-state={state} key={state}>
                  <span>{state}</span>
                  <strong>{label}</strong>
                </div>
              ))}
            </div>

            <svg
              className="investigation-graph"
              viewBox="0 0 1000 700"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <path d="M180 170 L380 120 L570 175 L790 280" />
              <path d="M180 170 L290 365 L505 340 L790 280" />
              <path d="M380 120 L505 340 L760 500" />
              <path d="M290 365 L520 545 L760 500" />
              <circle cx="505" cy="340" r="92" />
            </svg>

            <div className="investigation-context-frame" aria-hidden="true">
              <span>GLOBE LENS</span>
              <strong>INVESTIGATION_CONTEXT</strong>
              <span>GRAPH LENS</span>
              <small>The vector discovers · the graph contextualises · the runtime admits</small>
            </div>

            <div className="cinematic-dossier">
              <div className="dossier-live-head">
                <span>SCENE 06 · DOSSIER / SYNTHETIC</span>
                <i>TRACEABLE</i>
              </div>
              <h3>{m.dossier.title}</h3>
              <div className="dossier-live-meta">
                <span>{m.dossier.buyer}</span>
                <span>{m.dossier.location}</span>
                <span>{m.dossier.deadline}</span>
              </div>
              <div className="dossier-live-fields">
                {m.dossier.fields.map(([label, value]) => (
                  <div key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
              <p>{m.dossier.disclaimer}</p>
            </div>

            <div className="cinematic-profile">
              <span>{tedBoundedProductProfile.admissionState}</span>
              <p>{profileCopy.admitted}</p>
              <small>{profileCopy.boundary}</small>
            </div>

            <div className="cinematic-pricing-cue" aria-hidden="true">
              <span>PRICING + CONTROLLED ACCESS</span>
              <i>↓</i>
            </div>

            <ol className="cinematic-progress" id="cinematic-progress" aria-label="Product narrative">
              {sceneIds.map((scene, index) => (
                <li aria-current={activeScene === index ? "step" : undefined} key={scene}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <small>{scene.replace("SCENE_", "")}</small>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="reduced-story section-shell" aria-label="Product narrative">
          {sceneIds.map((scene, index) => {
            const sceneCopy = [
              [m.hero.title, m.hero.summary],
              [m.acts[2]?.title, m.acts[2]?.body],
              [m.acts[0]?.title, m.acts[0]?.body],
              [m.acts[4]?.title, m.acts[5]?.body],
              [m.acts[6]?.title, m.navigator.response],
              [m.dossier.title, m.acts[3]?.body]
            ][index];
            return (
              <article key={scene}>
                <span>{scene.replace("SCENE_", "")}</span>
                <h2>{sceneCopy?.[0]}</h2>
                <p>{sceneCopy?.[1]}</p>
              </article>
            );
          })}
        </section>

        <section className="status-ribbon" aria-label="Current product boundaries">
          <span>TED · PRODUCT_ADMITTED · PRIVATE_AUTHENTICATED_PILOT</span>
          <span>PUBLIC ACCESS · DISABLED</span>
          <span>UNRESTRICTED SOURCE USE · DISABLED</span>
          <span>DEMO DATA · SYNTHETIC</span>
        </section>

        <section className="pricing-section section-shell" id="pricing" data-section-reveal>
          <div className="section-heading">
            <p className="eyebrow">{m.pricing.eyebrow}</p>
            <h2>{plans.comparisonTitle}</h2>
            <p>{plans.comparisonBody}</p>
          </div>

          <article className="design-partner-band">
            <div>
              <span>{plans.designPartnerLabel}</span>
              <h3>{plans.designPartnerTitle}</h3>
              <p>{plans.designPartnerBody}</p>
            </div>
            <div>
              <small>{plans.indicative}</small>
              <strong>{plans.designPartnerPrice}</strong>
              <a
                className="button"
                href="#access"
                onClick={() => {
                  selectPlan("Design Partner");
                }}
              >
                {plans.designPartnerCta}
              </a>
            </div>
          </article>

          <div className="pricing-comparison-scroll" tabIndex={0}>
            <div className="pricing-comparison">
              <div className="comparison-corner">
                <span>{plans.indicative}</span>
                <strong>OPERATING BOUNDARY</strong>
              </div>
              {plans.plans.map((plan) => (
                <article className="plan-header" data-plan={plan.id} key={plan.id}>
                  <span>{plan.availability}</span>
                  <h3>{plan.name}</h3>
                  <strong>{plan.price}</strong>
                  <small>{plan.period}</small>
                  {plan.id === "controlled-trial" ? (
                    <ul className="trial-terms">
                      <li>7 days</li>
                      <li>1,000,000 cumulative tokens per organisation</li>
                      <li>No card</li>
                      <li>No automatic renewal</li>
                      <li>No overage</li>
                      <li>Read-only at expiry</li>
                    </ul>
                  ) : null}
                  <a
                    className={plan.id === "controlled-trial" ? "button" : "button button-ghost"}
                    href="#access"
                    onClick={() => selectPlan(plan.name)}
                  >
                    {plan.cta}
                  </a>
                </article>
              ))}

              {pricingRowKeys.map((rowKey, rowIndex) => (
                <div className="comparison-row" key={rowKey}>
                  <strong>{plans.rowLabels[rowKey]}</strong>
                  {plans.plans.map((plan) => (
                    <span key={`${plan.id}-${rowKey}`}>{plan.values[rowIndex]}</span>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="evidence-section section-shell" id="method" data-section-reveal>
          <div className="section-heading">
            <p className="eyebrow">{m.evidence.eyebrow}</p>
            <h2>{m.evidence.title}</h2>
            <p>{m.evidence.body}</p>
          </div>
          <div className="evidence-layout">
            <div className="claim-stack">
              {m.evidence.claims.map(([state, title, source], index) => (
                <article key={`${state}-${title}`}>
                  <span className="claim-index">{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <span className="state-chip" data-state={state}>
                      {state}
                    </span>
                    <h3>{title}</h3>
                    <p>{source}</p>
                  </div>
                </article>
              ))}
            </div>
            <div className="admission-pipeline">
              {m.evidence.pipeline.map((step, index) => (
                <div key={step}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{step}</strong>
                  {index < m.evidence.pipeline.length - 1 ? <i aria-hidden="true">↓</i> : null}
                </div>
              ))}
              <p>Proposal ≠ admission</p>
            </div>
          </div>
        </section>

        <section className="impact-section section-shell" data-section-reveal>
          <div className="section-heading">
            <p className="eyebrow">{m.outcomes.eyebrow}</p>
            <h2>{m.outcomes.title}</h2>
            <p>{m.outcomes.body}</p>
          </div>
          <ImpactCalculator locale={locale} messages={m.outcomes} />
        </section>

        <section className="problem-section section-shell" data-section-reveal>
          <div className="section-heading">
            <p className="eyebrow">{m.problem.eyebrow}</p>
            <h2>{m.problem.title}</h2>
            <p>{m.problem.body}</p>
          </div>
          <div className="problem-grid">
            {m.problem.items.map(([title, body], index) => (
              <article key={title}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="faq-section section-shell" id="faq" data-section-reveal>
          <div className="section-heading">
            <p className="eyebrow">{m.faq.eyebrow}</p>
            <h2>{m.faq.title}</h2>
          </div>
          <div className="faq-list">
            {m.faq.items.map(([question, answer], index) => (
              <details key={question} open={index === 0}>
                <summary>{question}</summary>
                <p>{answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="access-section section-shell" id="access" data-section-reveal>
          <div className="access-copy">
            <p className="eyebrow">{m.form.eyebrow}</p>
            <h2>{m.form.title}</h2>
            <p>{m.form.body}</p>
            <div className="access-boundaries">
              <span>APPLICATION · HUMAN REVIEW</span>
              <span>PUBLIC TRIAL · DISABLED</span>
              <span>NO SUBSCRIPTION CREATED</span>
            </div>
          </div>
          <PilotAccessForm locale={locale} messages={m.form} selectedPlan={selectedPlan} />
        </section>
      </main>

      <footer>
        <div className="footer-brand">
          <a className="brand-lockup" href={localePath(locale)} aria-label="AXIGNAL home">
            <Image
              className="brand-logo brand-logo-dark"
              src="/brand/axignal-logo-dark.svg"
              alt="AXIGNAL"
              width={1895}
              height={406}
            />
            <Image
              className="brand-logo brand-logo-light"
              src="/brand/axignal-logo.svg"
              alt=""
              width={1895}
              height={406}
              aria-hidden="true"
            />
          </a>
          <p>{m.footer.descriptor}</p>
        </div>
        <div className="footer-links">
          <a href="#method">{m.footer.methodology}</a>
          <a href="#method">{m.footer.trust}</a>
          <a href="/privacy">{m.footer.privacy}</a>
          <a href="/terms">{m.footer.terms}</a>
          <a href="/accessibility">{m.footer.accessibility}</a>
          <a href="#access" onClick={() => handleCta("footer")}>
            {m.nav.cta}
          </a>
        </div>
        <div className="footer-meta">
          <span>© 2026 AXIGNAL · axignal.com</span>
          <span>{m.footer.rights}</span>
        </div>
      </footer>
    </div>
  );
}
