# English essay live-provider release gate

**Milestone:** ENG-T3.10

**Required schema revision:** `202611020047`

**Default hosted state:** live provider disabled

ENG-T3.10 separates evidence collection from activation. A provider becomes available to a
learner only when all of these independent controls are current:

1. the latest report for the configured provider, model and policy passes the bounded ENG-T3.9
   calibration;
2. the latest privacy and safeguarding review for that exact report passes every check;
3. an academic administrator records an explicit release for that exact report and review;
4. the deployment environment switch is enabled; and
5. the learner has an unexpired guardian-consent grant for the configured consent policy.

Any missing or failed layer keeps live feedback unavailable. A newer calibration report or
privacy review invalidates an older release, so an approval cannot silently carry forward to
changed evidence. A suspension is immediate at the application gate. The environment switch
remains a separate operational circuit breaker.

## Bounded evidence

The administrator imports only the privacy-safe JSON produced by the offline T3.9 evaluator.
The API contract cannot accept raw essays, educator notes or provider responses. The stored
review contains booleans and opaque references for:

- guardian-consent process;
- retention and deletion policy;
- exclusion of raw essays from logs and analytics;
- provider agreement, subprocessor review and regional privacy review;
- provider data region and provider retention period;
- automated safety classification; and
- a named safeguarding contact held behind an opaque reference.

The application stores no guardian name, email or document. A learner consent event contains
only the learner ID, policy version, expiry, decision, audit reason and a SHA-256 reference to
the private consent record. Revocation is append-only and overrides the prior grant.

## Administrator workflow

The academic-administrator page at `/admin/essay-feedback` shows the current blockers and
privacy-safe aggregate. It supports four deliberate actions:

1. import an offline calibration report;
2. record the privacy and safeguarding review;
3. type the exact release or suspension phrase and an audit reason; and
4. record an opaque learner consent grant or revocation.

All writes are rate-limited and audited. Evidence, decisions and consent history are immutable.
The new tables are service-role only with row-level security enabled. Account-deletion preview
counts learner consent events, which are deleted with the learner account; administrative audit
records retain only their existing opaque references.

## Current operational state

No educator report, privacy approval, release decision or learner consent was fabricated while
implementing this milestone. No provider adapter was invoked and no paid token was spent.
Render must continue to set `ASEAN_ACADEMY_ENGLISH_ESSAY_FEEDBACK_ENABLED=false` until a
qualified educator and the responsible privacy/safeguarding owners complete the private work.

Changing the environment flag alone cannot open feedback. A configured provider/model identity,
PostgreSQL evidence, a current explicit release and current learner consent are also required.
