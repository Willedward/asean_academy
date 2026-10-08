# Capacity, infrastructure cost, and AI tutor model

**Status:** planning baseline  
**Prepared:** 2 October 2026  
**Currency:** USD unless stated otherwise  
**Architecture:** Next.js web, FastAPI Learning API, Supabase Auth/PostgreSQL, Render hosting

## Purpose

This document provides a conservative capacity and monthly cost model from internal beta
through 20,000 monthly active learners. It also records the recommended model policy for
the AI tutor and a per-student cost calculation.

These figures are planning ranges rather than vendor quotes or capacity guarantees. Every
production tier must pass an authenticated load test before promotion. Instance counts
should then be revised from observed CPU, memory, database, latency, and error data.

## Workload assumptions

The user counts in this document mean **monthly active users (MAU)**, not total registered
accounts. The unusually conservative peak assumption requested for planning is:

- 30–40% of MAU have a live session during a normal peak;
- a live non-AI session produces one application API action every 10 seconds on average;
- load tests apply a 2x burst above the average request rate;
- static assets and lesson media are served from a CDN/object store rather than FastAPI;
- answer marking remains deterministic and does not call an LLM;
- PostgreSQL uses Supabase's transaction pooler;
- expensive work such as email, analytics aggregation, imports, and AI follow-up jobs moves
  to background workers as scale increases.

This makes the planning load:

| MAU | Normal concurrent sessions | Average app API rate | 2x burst target |
| ---: | ---: | ---: | ---: |
| 10–50 | 3–20 | less than 1–2 requests/s | 4 requests/s |
| 100–200 | 30–80 | 3–8 requests/s | 16 requests/s |
| 500 | 150–200 | 15–20 requests/s | 40 requests/s |
| 1,000–2,000 | 300–800 | 30–80 requests/s | 160 requests/s |
| 10,000–20,000 | 3,000–8,000 | 300–800 requests/s | 1,600 requests/s |

If a live session actually generates one request every five seconds, these request-rate
targets double. Idle browser tabs, cached page reads, CDN traffic, and video playback must
not be counted as FastAPI requests.

## Executive budget

The recommended budget includes infrastructure, a controlled AI tutor allowance, and a
contingency margin. It excludes salaries, taxes, payment fees, referral commissions,
team AI subscriptions, and professional video hosting.

An illustrative conversion of **USD 1 = SGD 1.28** is used here. Actual invoices depend on
the settlement-date exchange rate and tax treatment.

| Stage | Platform before AI | AI reserve | Recommended total | Approximate SGD |
| --- | ---: | ---: | ---: | ---: |
| Internal beta, 10–50 MAU | $0–40 | $0–10 | **$0–50** | **S$0–64** |
| Private beta, 100–200 MAU | $120–220 | $25–100 | **$150–350** | **S$192–448** |
| Early production, 500 MAU | $275–475 | $125–250 | **$400–800** | **S$512–1,024** |
| Established beta, 1,000–2,000 MAU | $650–1,400 | $250–1,000 | **$1,000–2,500** | **S$1,280–3,200** |
| Growth, 10,000–20,000 MAU | $2,500–8,000 | $2,500–10,000 | **$6,000–20,000** | **S$7,680–25,600** |

The lower end assumes optimized database queries, CDN delivery, compact API payloads, and
measured AI usage. The upper end reserves capacity for high launch traffic, longer tutor
conversations, more workers, larger database compute, and operational tooling.

## Stage 1: internal beta, 10–50 MAU

| Component | Proposed configuration | Monthly cost |
| --- | --- | ---: |
| Render web | Free staging service | $0 |
| Render API | Free staging service | $0 |
| Supabase | Free/Nano staging project | $0 |
| Question source | Git-authored banks and database import | $0 |
| Object storage | Free allowance | $0 |
| Monitoring | Built-in dashboards and free uptime check | $0–10 |
| AI tutor | Synthetic/internal evaluation only | $0–10 |
| Domain | Optional, annual fee amortized | $1–3 |
| **Planning total** | | **$0–50** |

This tier is for reviewers and a small invited cohort. Render Free services sleep and do
not provide production scaling, so cold starts and occasional unavailability are expected.

## Stage 2: private beta, 100–200 MAU

At 30–40% concurrency this is 30–80 live sessions. Production services should be always on,
and the API should have two instances for availability and burst headroom.

| Component | Proposed configuration | Monthly cost |
| --- | --- | ---: |
| Render web | One 1 CPU / 2 GB instance | $25 |
| Render API | Two 1 CPU / 2 GB instances | $50 |
| Render worker | Small email/import worker | $7–25 |
| Render Key Value | Entry cache/rate-limit store | $10 |
| Supabase | Pro with Small compute after credit | $30 |
| Monitoring/email/storage/bandwidth | Entry allowances and reserves | $10–35 |
| AI tutor reserve | Capped student usage | $25–100 |
| Contingency | Traffic and invoice variance | $15–50 |
| **Planning total** | | **$150–350** |

Promotion criteria include successful authenticated tests at 16 requests/s, no database
connection exhaustion, acceptable p95 latency, and a tested backup restoration process.

## Stage 3: early production, 500 MAU

At 30–40% concurrency this is 150–200 live sessions and a 40 requests/s burst target.

| Component | Proposed configuration | Monthly cost |
| --- | --- | ---: |
| Render workspace | Pro when multiple engineers need platform access | $0–25 |
| Render web | Two 1 CPU / 2 GB instances | $50 |
| Render API | Two to three 1 CPU / 2 GB instances | $50–75 |
| Background worker | One 1 CPU / 2 GB worker | $25 |
| Key Value | 1 GB class or measured equivalent | $32 |
| Render bandwidth | Keep media off application services | $10–40 |
| Supabase | Pro with Medium compute after credit | $75 |
| Monitoring, email, storage, domain | | $30–80 |
| AI tutor reserve | | $125–250 |
| Contingency | | $30–100 |
| **Planning total** | | **$400–800** |

Scale instance counts from measured throughput rather than treating the table as a fixed
requirement. A highly optimized API may need fewer instances; synchronous heavy work may
need more.

## Stage 4: established beta, 1,000–2,000 MAU

At 30–40% concurrency this is 300–800 live sessions and a 160 requests/s burst target.

| Component | Proposed configuration | Monthly cost |
| --- | --- | ---: |
| Render Pro workspace | Shared production operations | $25 |
| Render web | Two to four 1 CPU / 2 GB instances | $50–100 |
| Render API | Four to eight 1 CPU / 2 GB instances, or fewer larger instances | $100–340 |
| Background workers | Two or more workers | $50–170 |
| Key Value | Cache, shared rate limits, short-lived state | $32–135 |
| Render bandwidth | API traffic only; media uses CDN/object store | $50–150 |
| Supabase | Pro with Medium or Large compute after credit | $75–125 |
| Monitoring, error tracking, email, storage | | $75–200 |
| AI tutor reserve | | $250–1,000 |
| Contingency | | $150–300 |
| **Planning total** | | **$1,000–2,500** |

Before opening this tier, run a sustained soak test as well as a short burst test. Monitor
database CPU, memory, active and pooler connections, slow queries, API CPU, queue delay,
and p95/p99 latency.

## Stage 5: growth, 10,000–20,000 MAU

The conservative assumption produces 3,000–8,000 live sessions, 300–800 average application
requests/s, and a 1,600 requests/s burst target. This is a substantial production system,
even though 20,000 registered accounts alone would not be difficult.

| Component | Proposed configuration | Monthly cost |
| --- | --- | ---: |
| Render workspace | Pro; reassess Scale only for governance requirements | $25–499 |
| Render web | Four to ten instances, sized from SSR measurements | $100–850 |
| Render API | Eight to twenty instances, sized from load tests | $200–1,700 |
| Background workers | Four to ten instances | $100–850 |
| Key Value | Larger cache/rate-limit tier | $135–550 |
| Render bandwidth | Strongly dependent on response sizes | $200–1,000 |
| Supabase primary | Large through 2XL after compute credit | $125–425 |
| Supabase read replica | Add only after measured read pressure | $0–410 |
| Monitoring, logs, email, storage, backup operations | | $300–1,200 |
| AI tutor reserve | | $2,500–10,000 |
| Contingency | | $500–2,000 |
| **Planning total** | | **$6,000–20,000** |

This does not yet require a microservice rewrite or Kubernetes. Preserve the modular
Next.js/FastAPI/Supabase architecture while separating background jobs and cache state.
Reconsider platforms only after measured cost, latency, availability, or regional constraints
show that the current providers are the limiting factor.

An influencer campaign must be modeled as a launch event rather than a normal peak. Protect
it with a CDN-served landing page, queue or throttle expensive signup work, store referral
attribution efficiently, and run a separate spike test before publication.

## AI tutor model recommendation

**Implementation note (8 October 2026):** The first hybrid router now keeps the configured
Gemini provider as the economy route and supports a pinned GPT-4o premium route. The
implemented score, S$0.017 representative GPT-4o turn estimate, reservation ceiling, and
activation gates are maintained in
[TUTOR_HYBRID_MODEL_ROUTING.md](TUTOR_HYBRID_MODEL_ROUTING.md). The older illustrative
Gemini Pro blend below remains a capacity-planning scenario rather than the implemented
premium target.

### Default model

Use **Gemini 2.5 Flash** as the first production tutor model, subject to the fixed mathematics
and answer-leakage evaluation described in `TUTOR_INTERACTION_DESIGN.md`.

Reasons:

- it is a reasoning-capable model rather than a lightweight classification model;
- it supports a thinking budget for harder explanations;
- its current paid standard rate is $0.30 per million text/image/video input tokens and
  $2.50 per million output tokens;
- it is inexpensive enough for a strict per-student quota;
- it can be used behind the planned provider interface and replaced without changing the
  tutor domain model.

### Supporting and escalation models

- Use **Gemini 2.5 Flash-Lite** for low-risk routing, intent classification, concise rewriting,
  and offline batch checks. Do not adopt it as the main mathematics tutor until it independently
  passes the same evaluation set.
- Allow **Gemini 2.5 Pro** only for a small controlled escalation path, such as repeated failure
  to explain a Level 4–5 concept. Cap this at approximately 5–10% of tutor turns initially.
- Do not let the model mark answers, change mastery, reveal locked solutions, or decide whether
  content is unlocked. Those decisions remain deterministic server responsibilities.

The free Gemini tier is acceptable for synthetic internal evaluation. Use the paid API tier
before real student conversations: the published pricing page states that free-tier data may
be used to improve Google's products, whereas paid-tier data is not used for that purpose.

Pin the model identifier and prompt-policy version, record token usage, and rerun the tutor
evaluation before every model or prompt change.

## Conservative AI cost per student

The costing model assumes an AI-active learner makes 60 tutor turns per month. Each turn has:

- 2,500 input tokens, including the relevant approved context and compact conversation history;
- 700 output tokens;
- 90% of turns on Gemini 2.5 Flash;
- 10% of turns escalated to Gemini 2.5 Pro;
- a 25% allowance for retries, safety processing, and usage variance.

At current published rates:

```text
Gemini 2.5 Flash turn
  2,500 input x $0.30 / 1M  = $0.00075
    700 output x $2.50 / 1M = $0.00175
  total                      = $0.00250

Gemini 2.5 Pro escalation turn
  2,500 input x $1.25 / 1M  = $0.003125
    700 output x $10.00 / 1M = $0.007000
  total                       = $0.010125

Blended turn
  90% x $0.00250 + 10% x $0.010125 = $0.0032625

60 turns x $0.0032625 x 1.25 allowance = approximately $0.245
```

Therefore the **conservative AI reserve is $0.25 per student per month** at 60 turns. A heavy
120-turn allowance is approximately **$0.50 per AI-active student per month** under the same
token profile. Long unrestricted transcripts can cost substantially more, which is why the
server must summarize or truncate context.

## Per-student monthly cost

The range below divides the full recommended stage budget by all MAU. It includes reserved AI
capacity, even though some students will not use it.

| Stage | Recommended total | Cost per MAU/month | Approximate SGD per MAU |
| --- | ---: | ---: | ---: |
| 100–200 MAU | $150–350 | **$0.75–3.50** | **S$0.96–4.48** |
| 500 MAU | $400–800 | **$0.80–1.60** | **S$1.02–2.05** |
| 1,000–2,000 MAU | $1,000–2,500 | **$0.50–2.50** | **S$0.64–3.20** |
| 10,000–20,000 MAU | $6,000–20,000 | **$0.30–2.00** | **S$0.38–2.56** |

For pricing and unit economics, use **US$2.50 per student per month** as an initial conservative
technical cost ceiling through the 2,000-user stage. This is intentionally above the expected
average and provides room for high concurrency and AI variance. It excludes payment fees,
support, content production, marketing, refunds, and referral commissions.

## Cost controls that must exist before enabling the tutor

1. Daily and monthly tutor-turn limits per learner.
2. Input, output, and total-token limits per turn.
3. One active generation per learner.
4. Compact, server-selected grounding instead of entire lesson or conversation histories.
5. Flash as the default, with audited Pro escalation.
6. Provider timeouts, bounded retries, and circuit breakers.
7. Per-learner and academy-wide usage ledgers.
8. Administrative cost dashboards and alerts at 50%, 75%, 90%, and 100% of budget.
9. A non-AI fallback using approved hints and worked solutions.
10. A kill switch that disables live tutoring without interrupting lessons or practice.

## Promotion gates

Do not promote a stage based only on registered-user count. Promote when the previous stage
reaches a sustained utilization or reliability threshold and the next stage passes:

- authenticated mixed read/write load testing at the listed burst target;
- a one-hour soak test and a launch-spike test;
- p95 and p99 latency targets agreed for each learner journey;
- database connection headroom and reviewed slow-query plans;
- successful backup restoration;
- worker queue recovery after an intentional provider failure;
- AI quota, leakage, model-quality, and spending-limit tests;
- operational alerts and a documented rollback procedure.

## Vendor price references

Prices were checked on 2 October 2026. Recheck before purchasing or changing tiers.

- [Render pricing](https://render.com/pricing)
- [Render compute plans](https://render.com/docs/compute-plans)
- [Render Free limitations](https://render.com/docs/free)
- [Supabase pricing](https://supabase.com/pricing)
- [Supabase compute usage and prices](https://supabase.com/docs/guides/platform/manage-your-usage/compute)
- [Supabase billing quotas](https://supabase.com/docs/guides/platform/billing-on-supabase)
- [Supabase MAU billing](https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users)
- [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Cloudflare R2 pricing](https://developers.cloudflare.com/r2/pricing/)

## Excluded costs

- salaries and contractor fees;
- Mathematics and editorial review labour;
- Codex, Claude, ChatGPT, or other team subscriptions;
- payment gateway fees, refunds, and chargebacks;
- influencer commission and referral payouts;
- tax, foreign exchange, and card fees;
- customer support;
- video production, transcoding, and professional streaming;
- legal, privacy, accounting, and compliance work.
