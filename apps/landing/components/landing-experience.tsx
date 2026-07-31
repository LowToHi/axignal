"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import {
  buyerProblems,
  citySignals,
  evidenceRail,
  frequentlyAskedQuestions,
  MESSAGE_VERSION,
  outcomeCards,
  storySteps,
  type CandidatePlan
} from "@/lib/landing-data";
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

function emitMessageEvent(event: string, location: string) {
  window.dispatchEvent(
    new CustomEvent("axignal:message-interaction", {
      detail: {
        event,
        location,
        messageVersion: MESSAGE_VERSION
      }
    })
  );
}

function formatPrice(plan: CandidatePlan) {
  return new Intl.NumberFormat("en", {
    style: "currency",
    currency: plan.currency,
    maximumFractionDigits: 0
  }).format(plan.amountMinor / 100);
}

type LandingExperienceProps = {
  plans: readonly CandidatePlan[];
};

export function LandingExperience({ plans }: LandingExperienceProps) {
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
          scrollTrigger: {
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
    <div
      ref={root}
      className="landing-root"
      data-message-version={MESSAGE_VERSION}
      data-testid="landing-experience"
    >
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
          <a href="#workflow">Workflow</a>
          <a href="#evidence">Evidence</a>
          <a href="#pricing">Plans</a>
          <a href="#access">Controlled access</a>
        </nav>
        <a
          className="header-cta"
          href="#access"
          onClick={() => emitMessageEvent("cta_click", "header")}
        >
          Request a workspace
        </a>
      </header>

      <main id="main-content">
        <section className="hero" id="top" aria-labelledby="hero-title">
          <div className="hero-noise" aria-hidden="true" />
          <div className="hero-copy">
            <p className="hero-kicker" data-reveal>
              EVIDENCE-BACKED RESEARCH FOR HIGH-STAKES DECISIONS
            </p>
            <h1 className="hero-title" id="hero-title" data-reveal>
              Turn scattered sources into a decision your team can verify.
              <span>Keep the evidence trail intact.</span>
            </h1>
            <p className="hero-summary" data-reveal>
              AXIGNAL brings research questions, sources, claims, uncertainty and review into one governed
              workspace. Strategy, investment and intelligence teams can move faster without rebuilding the
              trail in slides, chats and spreadsheets.
            </p>
            <div className="hero-actions" data-reveal>
              <a
                className="primary-button"
                href="#access"
                onClick={() => emitMessageEvent("cta_click", "hero_primary")}
              >
                Request a research workspace
              </a>
              <a
                className="secondary-button"
                href="#workflow"
                onClick={() => emitMessageEvent("workflow_view", "hero_secondary")}
              >
                See the research workflow
              </a>
            </div>
            <div className="hero-proof" data-reveal aria-label="Product boundaries">
              <span>Sources stay attached</span>
              <span>Uncertainty stays visible</span>
              <span>Review stays human</span>
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
            <span>SCROLL THROUGH THE WORKFLOW</span>
            <i />
          </div>
        </section>

        <section className="trust-strip" aria-label="Product principles">
          <span>Evidence before confidence</span>
          <span>Unknown stays unknown</span>
          <span>Proposal is not admission</span>
          <span>No autonomous decision authority</span>
        </section>

        <section className="problem-section" aria-labelledby="problem-title" data-section-reveal>
          <div className="section-heading">
            <p className="eyebrow">THE REAL RESEARCH COST</p>
            <h2 id="problem-title">
              The bottleneck is not access to information. It is proving why a decision deserves confidence.
            </h2>
            <p>
              Teams already have search, documents and AI summaries. What they often lose is the relationship
              between the question, the evidence, the disagreement and the final decision.
            </p>
          </div>
          <div className="problem-grid">
            {buyerProblems.map(([title, body], index) => (
              <article key={title}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="story-shell" id="workflow" ref={story} aria-label="Research workflow">
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
              <span className="hud-label">EVIDENCE STATE</span>
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

        <section className="evidence-section" id="evidence" data-section-reveal>
          <div className="section-heading">
            <p className="eyebrow">A REVIEWABLE EVIDENCE TRAIL</p>
            <h2>A conclusion is useful only when the team can inspect its support and failure conditions.</h2>
            <p>
              AXIGNAL separates observation, calculation, inference and contradiction. The summary does not
              erase the states that produced it.
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
                <strong>REVIEW</strong>
                <i />
                <span>ADMITTED</span>
              </div>
              <h3>AI can propose. It cannot silently admit a claim as truth.</h3>
              <p>
                Candidate claims pass deterministic checks. Human and policy gates determine what may be
                relied upon, shared or promoted.
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
            <p className="eyebrow">FROM RESEARCH TO REVIEW</p>
            <h2>Move faster without leaving the next reviewer a black box.</h2>
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

        <section className="pricing-section" id="pricing" data-section-reveal aria-labelledby="pricing-title">
          <div className="section-heading">
            <p className="eyebrow">CONTROLLED-ACCESS PACKAGES</p>
            <h2 id="pricing-title">Start with the team that owns the research decision.</h2>
            <p>
              These candidate packages are read from AXIGNAL&apos;s versioned server-side price book. They are
              shown for controlled-access evaluation only; public Stripe live checkout is not enabled.
            </p>
          </div>
          <div className="pricing-grid">
            {plans.map((plan) => (
              <article key={plan.planCode} data-testid={`plan-${plan.planCode.toLowerCase()}`}>
                <p className="eyebrow">{plan.activationState.replaceAll("_", " ")}</p>
                <h3>{plan.name}</h3>
                <p>{plan.description}</p>
                <div className="plan-price">
                  <strong>{formatPrice(plan)}</strong>
                  <span>/ {plan.billingPeriod}</span>
                </div>
                <p>
                  {plan.seatFloor}–{plan.seatCeiling} seats · bounded usage and technical quotas
                </p>
                <a
                  className="secondary-button"
                  href="#access"
                  onClick={() => emitMessageEvent("plan_interest", plan.planCode)}
                >
                  Discuss {plan.name}
                </a>
              </article>
            ))}
          </div>
          <p className="pricing-boundary">
            Candidate pricing is not a public offer. Taxes, commercial activation and live billing remain
            separate approval gates.
          </p>
        </section>

        <section className="assurance-section" data-section-reveal aria-labelledby="assurance-title">
          <div>
            <p className="eyebrow">BUILT FOR GOVERNED RESEARCH</p>
            <h2 id="assurance-title">Keep access, evidence and decision authority separate.</h2>
          </div>
          <ul>
            <li>Tenant and workspace authority resolved on the server</li>
            <li>Private evidence governed by classification, rights and retention</li>
            <li>Append-only records for material evidence and decisions</li>
            <li>Production, security and recovery objectives remain explicit gates</li>
          </ul>
          <p>
            These are implemented engineering controls and objectives. Public availability, production
            acceptance and Stripe live activation remain blocked until their independent evidence gates pass.
          </p>
        </section>

        <section className="faq-section" data-section-reveal aria-labelledby="faq-title">
          <div className="section-heading">
            <p className="eyebrow">QUESTIONS BEFORE ACCESS</p>
            <h2 id="faq-title">What AXIGNAL does—and what it does not claim.</h2>
          </div>
          <div className="faq-list">
            {frequentlyAskedQuestions.map(([question, answer]) => (
              <details key={question}>
                <summary>{question}</summary>
                <p>{answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="pilot-section" id="access" data-section-reveal>
          <div className="pilot-copy">
            <p className="eyebrow">CONTROLLED ACCESS</p>
            <h2>Bring one research decision that is expensive to get wrong.</h2>
            <p>
              Tell us what your team must decide, which sources it relies on and where the current workflow
              breaks. AXIGNAL will review whether the controlled programme can support that use case.
            </p>
            <div className="pilot-boundaries">
              <span>Access reviewed individually</span>
              <span>Live sources remain gated</span>
              <span>No subscription created by this form</span>
            </div>
          </div>
          <PilotAccessForm messageVersion={MESSAGE_VERSION} />
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
          <a href="#workflow">Workflow</a>
          <a href="#evidence">Evidence</a>
          <a href="#pricing">Plans</a>
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="/accessibility">Accessibility</a>
        </div>
        <span>© 2026 AXIGNAL · axignal.com</span>
      </footer>
    </div>
  );
}
