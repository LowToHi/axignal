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
  if (plan.amountMinor === 0) return "Free";

  return new Intl.NumberFormat("en", {
    style: "currency",
    currency: plan.currency,
    maximumFractionDigits: 0
  }).format(plan.amountMinor / 100);
}

function offerDetail(plan: CandidatePlan) {
  if (plan.billingPeriod === "trial") {
    return `${plan.aiTokenBudget?.toLocaleString("en")} AI tokens · no card · activation reviewed`;
  }

  return `${plan.seatFloor}–${plan.seatCeiling} seats · bounded usage and technical quotas`;
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
          <a href="#workflow">B2G workflow</a>
          <a href="#evidence">Evidence</a>
          <a href="#pricing">Trial & plans</a>
          <a href="#access">Request trial</a>
        </nav>
        <a
          className="header-cta"
          href="#access"
          onClick={() => emitMessageEvent("trial_request_click", "header")}
        >
          Request 7-day trial
        </a>
      </header>

      <main id="main-content">
        <section className="hero" id="top" aria-labelledby="hero-title">
          <div className="hero-noise" aria-hidden="true" />
          <div className="hero-copy">
            <p className="hero-kicker" data-reveal>
              BUSINESS-TO-GOVERNMENT (B2G) OPPORTUNITY INTELLIGENCE
            </p>
            <h1 className="hero-title" id="hero-title" data-reveal>
              Find the public contracts your business is built to pursue.
              <span>Turn global procurement into a qualified B2G pipeline.</span>
            </h1>
            <p className="hero-summary" data-reveal>
              AXIGNAL connects public tenders, contracting authorities, awards, suppliers and ownership
              signals so Business-to-Government teams can discover, qualify and investigate the opportunities
              worth pursuing—without losing the evidence behind the decision.
            </p>
            <div className="hero-actions" data-reveal>
              <a
                className="primary-button"
                href="#access"
                onClick={() => emitMessageEvent("trial_request_click", "hero_primary")}
              >
                Request your 7-day B2G trial
              </a>
              <a
                className="secondary-button"
                href="#workflow"
                onClick={() => emitMessageEvent("workflow_view", "hero_secondary")}
              >
                See a public-contract investigation
              </a>
            </div>
            <div className="hero-proof" data-reveal aria-label="B2G product boundaries">
              <span>Public contracts and tenders</span>
              <span>Buyer and award context</span>
              <span>Traceable evidence</span>
              <span>Human bid / no-bid authority</span>
            </div>
          </div>

          <div className="hero-orbit" aria-hidden="true">
            <div className="orbit-disc">
              <span />
              <span />
              <span />
            </div>
            <div className="orbit-caption">
              <b>SYNTHETIC B2G DEMONSTRATION</b>
              <span>Multiple markets · live sources disabled</span>
            </div>
          </div>

          <div className="scroll-cue" aria-hidden="true">
            <span>SCROLL THROUGH THE B2G WORKFLOW</span>
            <i />
          </div>
        </section>

        <section className="trust-strip" aria-label="Product principles">
          <span>Official-source lineage</span>
          <span>Unknown coverage stays unknown</span>
          <span>Proposal is not admission</span>
          <span>No autonomous bid authority</span>
        </section>

        <section className="problem-section" aria-labelledby="problem-title" data-section-reveal>
          <div className="section-heading">
            <p className="eyebrow">THE B2G PIPELINE PROBLEM</p>
            <h2 id="problem-title">Government demand is public. The opportunity is still fragmented.</h2>
            <p>
              Business-to-Government teams search across procurement portals, jurisdictions, languages,
              classifications, amendments and award records. By the time a tender reaches the pipeline, the
              deadline is close and the context needed for a disciplined bid / no-bid decision is scattered.
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

        <section className="story-shell" id="workflow" ref={story} aria-label="B2G opportunity workflow">
          <div className="globe-stage" ref={globeStage}>
            <div className="globe-aura" aria-hidden="true" />
            <SemanticGlobe activeStep={activeStep} reducedMotion={reducedMotion} />
            <div className="globe-grid" aria-hidden="true" />

            <div className="globe-topbar">
              <span className="live-dot" />
              <b>B2G OPPORTUNITY CONTEXT</b>
              <span>DEMO_PROCUREMENT_01</span>
              <span>AUTO</span>
              <span className="active-mode">GLOBE</span>
              <span>GRAPH</span>
            </div>

            <div className="globe-hud globe-hud-left">
              <span className="hud-label">NAVIGATOR</span>
              <p>Which public contracts fit our capabilities, target markets and delivery constraints?</p>
              <div className="navigator-response">
                <span>AXIGNAL</span>
                <p>{activeStory.detail}</p>
              </div>
            </div>

            <div className="globe-hud globe-hud-right">
              <span className="hud-label">QUALIFICATION STATE</span>
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
              <b>{activeCity.score}/100 synthetic fit score</b>
            </div>

            <div className="globe-progress" aria-hidden="true">
              {storySteps.map((step, index) => (
                <span key={step.id} className={index === activeStep ? "active" : ""} />
              ))}
            </div>

            <p className="synthetic-label">Synthetic demonstration · not procurement or win-rate evidence</p>
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
            <p className="eyebrow">FROM TENDER NOTICE TO INVESTIGATED OPPORTUNITY</p>
            <h2>Do not add a contract to the pipeline until the team can inspect why it belongs there.</h2>
            <p>
              AXIGNAL separates official observations, calculated fit, inferred relationships, contradictions
              and unknown conditions. The qualification summary does not erase the evidence states that
              produced it.
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
                <span>DISCOVERED</span>
                <i />
                <strong>QUALIFY</strong>
                <i />
                <span>PURSUE</span>
              </div>
              <h3>AI can propose a match. It cannot commit the company to a pursuit.</h3>
              <p>
                Candidate opportunities pass deterministic and human review. Business owners retain authority
                over qualification, partnerships, pricing, submissions and commercial commitments.
              </p>
              <ul>
                <li>Source and amendment lineage required</li>
                <li>Coverage limitations explicit</li>
                <li>Eligibility conflicts preserved</li>
                <li>Human bid / no-bid authority retained</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="outcomes-section" id="outcomes">
          <div className="section-heading" data-section-reveal>
            <p className="eyebrow">FROM PROCUREMENT VOLUME TO B2G PRIORITY</p>
            <h2>Spend pursuit effort on the public contracts your team can justify pursuing.</h2>
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
            <p className="eyebrow">TRIAL AND CONTROLLED-ACCESS PACKAGES</p>
            <h2 id="pricing-title">Prove the workflow on one real B2G market.</h2>
            <p>
              Request a controlled seven-day trial with a bounded 1,000,000-token AI budget and no card. If
              the workflow fits, continue with Professional or Team. Trial and paid activation remain reviewed;
              public Stripe live checkout is not enabled.
            </p>
          </div>
          <div className="pricing-grid pricing-grid-three">
            {plans.map((plan) => (
              <article key={plan.planCode} data-testid={`plan-${plan.planCode.toLowerCase()}`}>
                <p className="eyebrow">{plan.activationState.replaceAll("_", " ")}</p>
                <h3>{plan.name}</h3>
                <p>{plan.description}</p>
                <div className="plan-price">
                  <strong>{formatPrice(plan)}</strong>
                  <span>{plan.billingPeriod === "trial" ? `for ${plan.durationDays} days` : "/ month"}</span>
                </div>
                <p>{offerDetail(plan)}</p>
                <a
                  className={plan.billingPeriod === "trial" ? "primary-button" : "secondary-button"}
                  href="#access"
                  onClick={() => emitMessageEvent("offer_interest", plan.planCode)}
                >
                  {plan.ctaLabel}
                </a>
              </article>
            ))}
          </div>
          <p className="pricing-boundary">
            Candidate pricing is not a public offer. Trial eligibility, taxes, commercial activation and live
            billing remain separate approval gates.
          </p>
        </section>

        <section className="assurance-section" data-section-reveal aria-labelledby="assurance-title">
          <div>
            <p className="eyebrow">B2G INTELLIGENCE WITH A TRACEABLE BASIS</p>
            <h2 id="assurance-title">
              Know what came from the source, what AXIGNAL inferred and what your team decided.
            </h2>
          </div>
          <ul>
            <li>Official procurement records retain source and amendment lineage</li>
            <li>Missing, stale or contradictory coverage remains visible</li>
            <li>Tenant-private company capabilities remain separately governed</li>
            <li>AI proposes; humans retain bid, submission and commercial authority</li>
          </ul>
          <p>
            These are implemented engineering controls and objectives. Universal source coverage, public
            availability, production acceptance and Stripe live activation remain blocked until their
            independent evidence gates pass.
          </p>
        </section>

        <section className="faq-section" data-section-reveal aria-labelledby="faq-title">
          <div className="section-heading">
            <p className="eyebrow">B2G QUESTIONS BEFORE ACCESS</p>
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
            <p className="eyebrow">7-DAY CONTROLLED B2G TRIAL</p>
            <h2>Bring one public-procurement market your company wants to enter or qualify.</h2>
            <p>
              Tell us what your company sells to government, the countries or public buyers you target, the
              typical contract size and where the current tender workflow breaks. AXIGNAL will review whether
              the controlled trial can support that B2G use case.
            </p>
            <div className="pilot-boundaries">
              <span>7 days · 1,000,000 AI tokens</span>
              <span>No card or subscription</span>
              <span>Coverage confirmed before activation</span>
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
          <a href="#workflow">B2G workflow</a>
          <a href="#evidence">Evidence</a>
          <a href="#pricing">Trial & plans</a>
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="/accessibility">Accessibility</a>
        </div>
        <span>© 2026 AXIGNAL · axignal.com</span>
      </footer>
    </div>
  );
}
