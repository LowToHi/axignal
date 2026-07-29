"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { citySignals, evidenceRail, outcomeCards, storySteps } from "@/lib/landing-data";
import { PilotAccessForm } from "./pilot-access-form";

const SemanticGlobe = dynamic(
  () => import("./semantic-globe").then((module) => module.SemanticGlobe),
  {
    ssr: false,
    loading: () => <div className="globe-fallback" data-testid="globe-fallback" />
  }
);

function useReducedMotion() {
  const [reduced, setReduced] = useState(true);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return reduced;
}

export function LandingExperience() {
  const root = useRef<HTMLDivElement>(null);
  const story = useRef<HTMLElement>(null);
  const globeStage = useRef<HTMLDivElement>(null);
  const [activeStep, setActiveStep] = useState(0);
  const reducedMotion = useReducedMotion();

  const activeStory = storySteps[activeStep] ?? storySteps[0]!;
  const activeCity = useMemo(
    () => citySignals[Math.max(0, Math.min(citySignals.length - 1, activeStep - 2))] ?? citySignals[0]!,
    [activeStep]
  );

  useEffect(() => {
    if (!root.current) return;

    gsap.registerPlugin(ScrollTrigger);
    const matchMedia = gsap.matchMedia();
    const context = gsap.context(() => {
      gsap.set("[data-reveal]", { autoAlpha: 1 });

      matchMedia.add("(prefers-reduced-motion: no-preference) and (min-width: 901px)", () => {
        gsap.from(".hero-kicker, .hero-title, .hero-summary, .hero-actions, .hero-proof", {
          y: 28,
          autoAlpha: 0,
          duration: 1.05,
          stagger: 0.11,
          ease: "power3.out"
        });

        if (story.current && globeStage.current) {
          ScrollTrigger.create({
            trigger: story.current,
            start: "top top",
            end: "bottom bottom",
            pin: globeStage.current,
            pinSpacing: false,
            anticipatePin: 1
          });
        }

        const steps = gsap.utils.toArray<HTMLElement>("[data-story-step]");
        steps.forEach((step, index) => {
          ScrollTrigger.create({
            trigger: step,
            start: "top 58%",
            end: "bottom 42%",
            onEnter: () => setActiveStep(index),
            onEnterBack: () => setActiveStep(index)
          });

          gsap.fromTo(
            step,
            { autoAlpha: 0.25, y: 34 },
            {
              autoAlpha: 1,
              y: 0,
              ease: "none",
              scrollTrigger: {
                trigger: step,
                start: "top 82%",
                end: "top 54%",
                scrub: true
              }
            }
          );
        });

        gsap.to(".globe-aura", {
          scale: 1.18,
          opacity: 0.72,
          ease: "none",
          scrollTriggger: {
            trigger: story.current,
            start: "top top",
            end: "bottom bottom",
            scrub: 1.2
          }
        });

        gsap.utils.toArray<HTMLElement>("[data-section-reveal]").forEach((section) => {
          gsap.from(section, {
            y: 48,
            autoAlpha: 0,
            duration: 0.9,
            ease: "power3.out",
            scrollTrigger: {
              trigger: section,
              start: "top 82%",
              once: true
            }
          });
        });
      });

      matchMedia.add("(prefers-reduced-motion: reduce), (max-width: 900px)", () => {
        const steps = gsap.utils.toArray<HTMLElement>("[data-story-step]");
        steps.forEach((step, index) => {
          ScrollTrigger.create({
            trigger: step,
            start: "top 65%",
            onEnter: () => setActiveStep(index),
            onEnterBack: () => setActiveStep(index)
          });
        });
      });
    }, root);

    return () => {
      matchMedia.revert();
      context.revert();
    };
  }, []);

  return (
    <div ref={root} className="landing-root">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <header className="site-header">
        <a className="brand-lockup" href="#top" aria-label="AXIGNAL home">
          <span className="brand-mark" aria-hidden="true">
            ⌁
          </span>
          <span>AXIGNAL</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#investigation">Product</a>
          <a href="#method">Method</a>
          <a href="#outcomes">Outcomes</a>
          <a href="#access">Private pilot</a>
        </nav>
        <a className="header-cta" href="#access">
          Request access
        </a>
      </header>

      <main id="main-content">
        <section className="hero" id="top">
          <div className="hero-noise" aria-hidden="true" />
          <div className="hero-copy">
            <p className="hero-kicker" data-reveal>
              GLOBAL OPPORTUNITY INTELLIGENCE
            </p>
            <h1 className="hero-title" data-reveal>
              Discover what is changing
              <span>before it becomes obvious.</span>
            </h1>
            <p className="hero-summary" data-reveal>
              AXIGNAL turns fragmented global signals into persistent, evidence-backed investigations across
              geography, relationships, time, claims and sources.
            </p>
            <div className="hero-actions" data-reveal>
              <a className="primary-button" href="#access">
                Request private access
              </a>
              <a className="secondary-button" href="#investigation">
                Explore the investigation
              </a>
            </div>
            <div className="hero-proof" data-reveal>
              <span>Traceable claims</span>
              <span>Contradictions visible</span>
              <span>Human authority preserved</span>
            </div>
          </div>

          <div className="hero-orbit" aria-hidden="true">
            <div className="orbit-disc">
              <span />
              <span />
              <span />
            </div>
            <div className="orbit-caption">
              <b>SYNTHETIC DEMONSTRATION</b>
              <span>Europe · live sources disabled</span>
            </div>
          </div>

          <div className="scroll-cue" aria-hidden="true">
            <span>SCROLL TO INVESTIGATE</span>
            <i />
          </div>
        </section>

        <section className="trust-strip" aria-label="Product principles">
          <span>Evidence before confidence</span>
          <span>Unknown stays unknown</span>
          <span>Proposal is not admission</span>
          <span>No execution or custody</span>
        </section>

        <section className="story-shell" id="investigation" ref={story}>
          <div className="globe-stage" ref={globeStage}>
            <div className="globe-aura" aria-hidden="true" />
            <SemanticGlobe activeStep={activeStep} reducedMotion={reducedMotion} />
            <div className="globe-grid" aria-hidden="true" />

            <div className="globe-topbar">
              <span className="live-dot" />
              <b>INVESTIGATION CONTEXT</b>
              <span>DEMO_EUROPE_01</span>
              <span>AUTO</span>
              <span className="active-mode">GLOBE</span>
              <span>GRAPH</span>
            </div>

            <div className="globe-hud globe-hud-left">
              <span className="hud-label">NAVIGATOR</span>
              <p>Where are infrastructure, policy and capital signals converging?</p>
              <div className="navigator-response">
                <span>AXIGNAL</span>
                <p>{activeStory.detail}</p>
              </div>
            </div>

            <div className="globe-hud globe-hud-right">
              <span className="hud-label">SIGNAL STATE</span>
              <strong>{activeStory.signal}</strong>
              <p>{activeStory.metric}</p>
              <div className="state-chip" data-state={activeStory.claimState}>
                {activeStory.claimState}
              </div>
            </div>

            <div className="globe-location-card">
              <span>{activeCity.country}</span>
              <strong>{activeCity.city}</strong>
              <p>{activeCity.label}</p>
              <b>{activeCity.score}/100 synthetic score</b>
            </div>

            <div className="globe-progress" aria-hidden="true">
              {storySteps.map((step, index) => (
                <span key={step.id} className={index === activeStep ? "active" : ""} />
              ))}
            </div>

            <p className="synthetic-label">Synthetic demonstration · not investment performance</p>
          </div>

          <div className="story-steps">
            {storySteps.map((step, index) => (
              <article
                className={index === activeStep ? "story-step active" : "story-step"}
                data-story-step
                data-step={index}
                key={step.id}
              >
                <span className="step-index">{step.index}</span>
                <p className="eyebrow">{step.eyebrow}</p>
                <h2>{step.title}</h2>
                <p>{step.body}</p>
                <div className="step-evidence">
                  <span data-state={step.claimState}>{step.claimState}</span>
                  <b>{step.signal}</b>
                  <small>{step.metric}</small>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="evidence-section" id="method" data-section-reveal>
          <div className="section-heading">
            <p className="eyebrow">TRUST BY CONSTRUCTION</p>
            <h2>A conclusion is only useful when its evidence and failure conditions are visible.</h2>
            <p>
              AXIGNAL separates observation, calculation, inference and contradiction. Every state remains
              inspectable inside the investigation.
            </p>
          </div>

          <div className="evidence-layout">
            <div className="claim-stack">
              {evidenceRail.map((item, index) => (
                <article key={item.title}>
                  <span className="claim-number">{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <span className="state-chip" data-state={item.state}>
                      {item.state}
                    </span>
                    <h3>{item.title}</h3>
                    <p>{item.source}</p>
                  </div>
                  <time>{item.freshness}</time>
                </article>
              ))}
            </div>

            <div className="admission-panel">
              <div className="admission-core" aria-hidden="true">
                <span>CANDIDATE</span>
                <i />
                <strong>ADMISSION</strong>
                <i />
                <span>CANONICAL</span>
              </div>
              <h3>Deterministic admission boundary</h3>
              <p>
                Models may propose evidence and Candidate Claims. They cannot silently convert a proposal into
                canonical truth.
              </p>
              <ul>
                <li>Provenance required</li>
                <li>Coverage explicit</li>
                <li>Contradictions preserved</li>
                <li>Human acceptance bounded</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="outcomes-section" id="outcomes">
          <div className="section-heading" data-section-reveal>
            <p className="eyebrow">ONE PERSISTENT INSTRUMENT</p>
            <h2>Move from discovery to defensible understanding without losing context.</h2>
          </div>
          <div className="outcome-grid">
            {outcomeCards.map(([title, body], index) => (
              <article key={title} data-section-reveal>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="pilot-section" id="access" data-section-reveal>
          <div className="pilot-copy">
            <p className="eyebrow">PRIVATE PILOT</p>
            <h2>Bring one high-cost research question.</h2>
            <p>
              AXIGNAL is preparing a bounded private pilot for qualified professionals. Access is reviewed
              individually; deployment status and commercial terms are not represented as complete.
            </p>
            <div className="pilot-boundaries">
              <span>Private access only</span>
              <span>Live sources gated</span>
              <span>No public performance claims</span>
            </div>
          </div>
          <PilotAccessForm />
        </section>
      </main>

      <footer>
        <a className="brand-lockup" href="#top" aria-label="AXIGNAL home">
          <span className="brand-mark" aria-hidden="true">
            ⌁
          </span>
          <span>AXIGNAL</span>
        </a>
        <div>
          <a href="#investigation">Product</a>
          <a href="#method">Methodology</a>
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="/accessibility">Accessibility</a>
        </div>
        <span>© 2026 AXIGNAL · axignal.com</span>
      </footer>
    </div>
  );
}
