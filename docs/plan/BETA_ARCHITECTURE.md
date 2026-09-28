# ASEAN Academy beta architecture

**Implementation snapshot:** 28 September 2026, `feature/authenticated-beta-e2e`.
**Companions:** [Content synchronization and admin runbook](CONTENT_SYNC_ADMIN_DASHBOARD.md) and [Content review and controlled publication](CONTENT_REVIEW_PUBLICATION.md).
**Format:** Markdown with editable Mermaid diagrams. GitHub renders these diagrams; a
Mermaid-enabled Markdown preview can render them locally. The overview is also supplied
as [BETA_ARCHITECTURE.mmd](BETA_ARCHITECTURE.mmd) for Mermaid editors and SVG/PDF export.
Use SVG for a large, zoomable exported diagram; JPEG makes small labels harder to read.

## 1. Boundaries and implementation status

The beta has **two application processes**: a Next.js web server and a Python FastAPI
Learning API. It uses managed Supabase Auth and PostgreSQL. The API is a modular
application: identity, course, practice, progress and administration are code modules
inside the same process, not separately deployed microservices. The question-bank
package is an imported Python library and command-line tool.

This keeps deployment, transactions and debugging manageable at beta scale. Split a
module into a separate service only when scaling, isolation or ownership requires it.

| Component | Responsibility | Current status / location |
| --- | --- | --- |
| Web | Student and administrator pages, Google sign-in, session cookies, same-origin API proxy, KaTeX | Implemented, `apps/web`; design remains replaceable |
| Learning API | Verified identity, access rules, lesson/practice workflows, progress, administration | Implemented, `services/learning_api` |
| Supabase Auth | Google OAuth exchange, user identity, access/refresh tokens | Integrated; Google/Supabase dashboard configuration is external |
| PostgreSQL | Imported content revisions, profiles, invitations, enrolments, attempts, progress, audit | Implemented, `supabase/migrations` |
| Question-bank domain | Validation, numeric/expression checking, hints, solutions, content import | Implemented shared package, `question_bank` |
| Git-authored content | Editable, reviewable source for lessons and questions | 40 N1 question drafts; seven lesson records; Lesson 1 has draft notes |
| CI and release tooling | Unit/contract tests, authenticated browser journeys, migration checks, imports, deployment sequencing, health checks | Workflows implemented; actual Railway/GitHub configuration must be verified separately |
| OCR and categorization | PDF extraction, staging/review and syllabus mapping | Existing offline tools; outside the student request path |
| Conversational AI tutor | Grounded follow-up explanations and multi-turn conversation | Planned; current hints/solutions are authored content, not live LLM responses |
| Video delivery | Hosted media, captions/transcript, playback | Pending media and hosting decision; lesson page has placeholder support |

## 2. System and network overview

Solid arrows represent implemented dependencies. Dashed arrows represent future integrations.
Hosted service names are logical names; no IP addresses or production URLs are assumed.

```mermaid
flowchart TB
  subgraph people["Users and authoring"]
    STUDENT["Student browser"]
    ADMIN["Administrator browser"]
    AUTHOR["Content author and reviewer"]
  end

  subgraph web["Next.js web service — localhost:3000 in development"]
    PAGES["Course map · Lesson notes · Practice · Progress"]
    DASH["Admin overview · Students · Questions<br/>Content review · Invitations · Roles · Audit · Operations"]
    SESSION["Server session verification<br/>OAuth callback and cookie refresh"]
    PROXY["Same-origin /api/v1/* proxy<br/>No-store responses · Request IDs"]
    PAGES --> PROXY
    DASH --> PROXY
    SESSION --> PROXY
  end

  subgraph api["FastAPI Learning API — localhost:8000 in development"]
    AUTHZ["Token verification and database role checks"]
    COURSE["Course catalogue and prerequisites"]
    PRACTICE["Practice orchestration and deterministic marking"]
    PROGRESS["Section progress · Proficiency · Checkpoint mastery"]
    OPS["Admin analytics · Invitations · Role management"]
    REVIEW["Content review · Safe preview · Release requests"]
    SYNC["Content hashes · Readiness · Revision migration"]
    AUTHZ --> COURSE
    AUTHZ --> PRACTICE
    AUTHZ --> PROGRESS
    AUTHZ --> OPS
    AUTHZ --> REVIEW
    OPS --> SYNC
    PRACTICE --> PROGRESS
  end

  subgraph supabase["Supabase managed services"]
    AUTH["Supabase Auth"]
    DB[("PostgreSQL<br/>Content revisions and learner state")]
  end

  GOOGLE["Google OAuth"]
  BANK["question_bank Python library<br/>Validation · Checking · Importers"]
  GIT[("Git-authored JSON and assets")]
  CI["GitHub Actions<br/>Validate → Migrate → Approval gate → Import → Deploy → Smoke"]
  OCR["Offline OCR and categorizer<br/>Staging and human review"]
  AI["Future grounded AI tutor"]
  VIDEO["Future video host and captions"]

  STUDENT --> PAGES
  ADMIN --> DASH
  STUDENT --> SESSION
  ADMIN --> SESSION
  SESSION --> AUTH
  AUTH <-->|OAuth| GOOGLE
  PROXY -->|"Bearer token / HTTP"| AUTHZ
  AUTHZ -->|"JWKS or Auth user verification"| AUTH
  AUTHZ -->|"profiles.role"| DB
  COURSE --> GIT
  PRACTICE --> BANK
  PROGRESS --> DB
  PRACTICE --> DB
  OPS --> DB
  REVIEW --> DB
  REVIEW --> GIT
  SYNC --> DB
  SYNC --> GIT
  BANK --> GIT
  AUTHOR --> GIT
  AUTHOR --> OCR
  OCR -.->|"Reviewed future ingestion"| GIT
  GIT --> CI
  CI -->|"Migrations and content imports"| DB
  CI -->|"Deploy API then web"| api
  CI --> web
  PRACTICE -.-> AI
  PAGES -.-> VIDEO

  classDef managed fill:#ede9fe,stroke:#7c3aed,color:#111827
  classDef future fill:#f8fafc,stroke:#94a3b8,stroke-dasharray:5 5,color:#475569
  classDef data fill:#fef3c7,stroke:#d97706,color:#111827
  class AUTH,DB,GOOGLE managed
  class AI,VIDEO future
  class GIT data
```

### Connections and trust boundaries

| From → to | Transport / address | Identity and restrictions |
| --- | --- | --- |
| Browser → web | HTTP localhost:3000; HTTPS when hosted | Supabase-backed browser session; admin server guards |
| Web → API | HTTP localhost:8000; configured `LEARNING_API_URL` when hosted | Verified session access token forwarded as Bearer; browser-supplied role is not trusted |
| Web → Supabase Auth | HTTPS project URL | Publishable key and OAuth session; publishable key is not a DB password |
| API → Supabase Auth | HTTPS JWKS; legacy-token fallback to Auth user endpoint | Checks token signature/issuer/audience/expiry or asks Auth to verify |
| API → PostgreSQL | psycopg using saved server-only database URL | Explicit ownership/role checks plus database RLS where applicable |
| Bootstrap / release → PostgreSQL | Administrative migration/import connection | Server-side secret; never a frontend variable |
| Google → Supabase | OAuth callback `https://<project>.supabase.co/auth/v1/callback` | Google client ID/secret configured in Supabase provider |
| Supabase → web | Allowed application `/auth/callback` | Application exchanges code and establishes cookies |

Supabase PostgREST is not the application's learning-data access path. Database
credentials remain on the API/release side. An owner-level DB connection can bypass
RLS; application ownership and role checks remain essential. Do not treat RLS as
a substitute for endpoint authorization.

## 3. API module map

```mermaid
flowchart LR
  ROUTES["FastAPI routers"]
  DEP["dependencies.py<br/>Authenticated identity · Role and repository dependencies"]
  ID["identity.py<br/>SupabaseTokenVerifier"]
  IDREPO["identity_repository.py<br/>Profiles · Invitations · Enrolment"]
  CAT["course_catalogue.py<br/>Validated deployed JSON snapshot"]
  PS["practice_service.py<br/>Guided / retry / checkpoint orchestration"]
  PE["postgres_practice.py<br/>Session ownership · Idempotency · Attempt persistence"]
  CHECK["question_bank/checking.py<br/>Deterministic answers"]
  GS["progress_service.py<br/>Prerequisites and mastery policies"]
  GR["progress_repository.py<br/>PostgreSQL or local SQLite"]
  ADMIN["admin_repository.py<br/>Invitations · Audit · Service status"]
  ANALYTICS["admin_analytics_repository.py<br/>Students · Questions · Roles"]
  REVIEW["content_review.py<br/>Fingerprint · Decisions · Release requests"]
  TRANSITION["curriculum_admin.py<br/>Preview · Lock · Check · Update · Audit"]
  HEALTH["content_sync.py<br/>Revision and content-hash checks"]
  PG[("PostgreSQL")]
  ROUTES --> DEP
  DEP --> ID
  ROUTES --> IDREPO
  ROUTES --> CAT
  ROUTES --> PS
  PS --> PE
  PE --> CHECK
  PS --> GS
  GS --> GR
  ROUTES --> ADMIN
  ROUTES --> ANALYTICS
  ROUTES --> REVIEW
  ROUTES --> TRANSITION
  TRANSITION --> HEALTH
  IDREPO --> PG
  PE --> PG
  GR --> PG
  ADMIN --> PG
  ANALYTICS --> PG
  REVIEW --> PG
  TRANSITION --> PG
  HEALTH --> PG
```

These modules run in one API process. There is no Redis, message broker, Kubernetes
cluster, asynchronous marking worker or independent analytics warehouse in the beta.

## 4. Sign-in and onboarding sequence

```mermaid
sequenceDiagram
  actor User
  participant Web as Next.js
  participant Auth as Supabase Auth
  participant Google
  participant API as Learning API
  participant DB as PostgreSQL

  User->>Web: Continue with Google
  Web->>Auth: OAuth sign-in request
  Auth->>Google: Consent and account selection
  Google-->>Auth: OAuth authorization result
  Auth-->>Web: Redirect to application callback
  Web->>Auth: Exchange authorization code
  Auth-->>Web: User session
  Web->>API: Request learner with Bearer token
  API->>Auth: Verify via JWKS or legacy Auth endpoint
  API->>DB: Read profile and active enrolments
  alt No registered profile
    API-->>Web: Onboarding required
    User->>Web: Name and invitation code
    Web->>API: Submit onboarding
    API->>DB: Validate email, hashed code, expiry and use limit
    API->>DB: Create profile and pinned enrolment, audit acceptance
    API-->>Web: Learner profile
  else Existing account
    API-->>Web: Profile and database-backed role
  end
  Web-->>User: Learner view or protected admin view
```

Signing in identifies a person; an invitation authorizes entry to the beta.
An administrator role is stored in `profiles.role`, not assigned by an email string
in the UI or by untrusted user metadata. Google login alone does not prevent account
sharing; device/session policy would be a separate future feature.

## 5. Learning, answers and progress

```mermaid
sequenceDiagram
  actor Student
  participant Web
  participant API as Course / Practice / Progress API
  participant Checker as Deterministic checker
  participant DB as PostgreSQL

  Student->>Web: Open lesson
  Web->>API: Request lesson and learner progress
  API->>DB: Check enrolment / progress / prerequisites
  API-->>Web: Public lesson blocks, locked answers omitted
  Student->>Web: Complete reading or answer active recall
  Web->>API: Explicit completion or recall answer
  API->>Checker: Check active recall when applicable
  API->>DB: Record exact section revision
  Student->>Web: Start guided practice
  Web->>API: Create session with idempotency key
  API->>DB: Lock learner, verify enrolment pin, create/resume session
  API-->>Web: Session and question prompt
  Student->>Web: Submit numeric / expression fields
  Web->>API: Answer map and idempotency key
  API->>Checker: Evaluate authored answer specification
  API->>DB: Persist attempt and per-question progress
  API->>DB: Synchronize lesson progress / checkpoint evidence
  API-->>Web: Feedback and policy-permitted explanation
  Student->>Web: Ask for hint / give up / continue
  Web->>API: Session-scoped action
  API-->>Web: Authored hint or worked solution under session policy
```

- Marks, two hints and worked solutions live with each question revision.
- Submitted final answers are checked deterministically; handwriting OCR is not required.
- Reading completion records engagement, not mastery.
- Guided practice, retry review and checkpoint policies differ; checkpoint feedback
  remains governed by its assessment rules.
- Author-defined lesson pools have an explicit sequence; they are not all randomized.
  The shared practice engine supports adaptive selection, and required retries are
  selected from recorded unresolved evidence.
- Attempt writes are idempotent. Practice persistence and progress synchronization
  span service operations; repeated summary reads reconcile progress. There is no
  claim of a distributed transaction or message queue.
- Live conversational tutoring is still future work. Showing an authored full solution
  does not mean an LLM has been called.

## 6. Database relationships

The following ER diagram groups the main real tables. It omits secondary indexes and
some columns for readability; migration SQL remains the authoritative schema.

```mermaid
erDiagram
  auth_users ||--o| profiles : identifies
  auth_users ||--o{ course_enrolments : owns
  courses ||--o{ course_versions : versions
  courses ||--o{ course_enrolments : enrols
  course_versions ||--o{ course_enrolments : pins
  course_versions ||--o{ unit_versions : contains
  unit_versions ||--o{ unit_version_lessons : maps
  lesson_versions ||--o{ unit_version_lessons : appears_in
  course_lessons ||--o{ lesson_versions : versions
  lesson_versions ||--o{ lesson_sections : contains
  lesson_versions ||--o{ lesson_question_pools : allocates
  lesson_question_pools ||--o{ lesson_question_pool_items : selects
  math_question_versions ||--o{ lesson_question_pool_items : supplies
  math_questions ||--o{ math_question_versions : versions
  math_question_versions ||--o{ math_question_parts : contains
  math_question_parts ||--o| math_answer_specs : checks
  math_question_parts ||--o{ math_question_hints : supports
  math_question_parts ||--o{ math_solution_steps : explains
  auth_users ||--o{ practice_sessions : owns
  practice_sessions ||--o{ session_questions : selects
  math_question_versions ||--o{ session_questions : pins
  session_questions ||--o{ attempts : receives
  auth_users ||--o{ question_progress : accumulates
  auth_users ||--o{ learner_lesson_progress : records
  lesson_versions ||--o{ learner_lesson_progress : pins
  auth_users ||--o{ learner_lesson_section_progress : records
  lesson_sections ||--o{ learner_lesson_section_progress : completes
  auth_users ||--o{ mastery_events : earns
  auth_users ||--o{ beta_audit_events : acts_or_is_target
  profiles ||--o{ content_review_records : reviews
  profiles ||--o{ content_lifecycle_requests : requests
  beta_invitations ||--o{ beta_audit_events : relates
```

Additional tables include curriculum versions, syllabus topics/outcomes, programmes,
mastery policies, lesson prerequisites/assets/outcomes, unit checkpoint pools and
practice creation idempotency keys. A question's stable key identifies it across
revisions; attempts and session items refer to exact persisted versions.

### Who owns which data?

| Data | Source of truth | Read/write path |
| --- | --- | --- |
| Authored lessons/questions | Reviewed Git JSON and assets | Validator → importer → immutable DB revisions |
| Runtime course display | Validated snapshot shipped with API | Catalogue reads deployed JSON; readiness verifies corresponding DB hashes |
| User identity | Supabase Auth | OAuth and token verification |
| Role, invitation, course pin | PostgreSQL | Authorized identity/admin APIs |
| Attempts and progress | PostgreSQL in hosted mode | Student-scoped API and repositories |
| Local unauthenticated preview | SQLite | Development-only fallback; not automatically merged into hosted accounts |
| Aggregated admin metrics | PostgreSQL query results | Protected API; no separate analytics copy |
| Review decisions and lifecycle requests | Append-only PostgreSQL records bound to a Git-content fingerprint | Protected content-review API; release gate reads them |
| Release identity and request logs | Process environment and logs | Health/status endpoints and hosting log system |

**Important limitation:** the current API serves one bundled N1 catalogue. Importing
multiple revisions does not create a full arbitrary historical-catalogue server.
Existing sessions can resume only while their question revisions remain supported
by the deployed engine. Keep those revisions available and test active sessions
before shipping question revisions. This milestone adds explicit migration guards,
not unrestricted historical course delivery.

## 7. Content authoring, synchronization and release

```mermaid
flowchart TB
  SOURCE["Edit draft question / course JSON"]
  VALIDATE["Schema · Syllabus · Answer · Pool validation"]
  PREVIEW["Student-safe preview"]
  MATH["Mathematics review"]
  EDIT["Editorial review"]
  APPROVED["Both latest decisions approve the semantic fingerprint"]
  REQUEST["Academic publication request"]
  GITREV["Reviewed / published Git revision"]
  GATE["Automated approval and content release gate"]
  IMPORT["Question importer then course importer"]
  HASH["Immutable revision hashes match deployed catalogue"]
  DB[("PostgreSQL content and append-only decisions")]
  START["API startup content check"]
  READY["/api/v1/ready<br/>Schema and content checks"]
  TRAFFIC["Accept new deployment traffic"]

  SOURCE --> VALIDATE
  VALIDATE -->|"Development preview allowed"| IMPORT
  VALIDATE --> PREVIEW
  PREVIEW --> MATH
  PREVIEW --> EDIT
  MATH --> APPROVED
  EDIT --> APPROVED
  APPROVED --> REQUEST
  REQUEST --> GITREV
  GITREV --> GATE
  GATE -->|"Approved"| IMPORT
  GATE -->|"Missing or stale decision"| STOP["Stop release and return to review"]
  IMPORT --> DB
  DB --> HASH
  HASH --> START
  START --> READY
  READY -->|"Ready"| TRAFFIC
  READY -->|"Mismatch"| STOP2["Stop promotion; import or repair first"]
```


Importing a draft is allowed for development and does **not** publish it. Production
configuration refuses draft visibility. Current N1 content still needs review.
A repeated import accepts the same immutable revision and rejects changed content
under the same revision. Increment revisions for meaningful content changes.

Local `bootstrap:api` previews first and applies only with `--apply`. It uses the
existing saved connection, checks migration history, applies pending migrations
with a ledger entry in each transaction, and imports content transactionally.
It does not reset credentials, create invitations or migrate enrolments.

## 8. Safe learner course updates

```mermaid
flowchart TD
  OPEN["Academic admin opens Users and roles"]
  PREVIEW["Preview target served revision"]
  CHECK["Compare source pin, target hash,<br/>active sessions and existing lesson evidence"]
  BLOCK["Show blockers; preserve current enrolment"]
  CONFIRM["Admin supplies reason and confirms"]
  LOCK["Acquire learner transaction lock"]
  RECHECK["Recheck preview and blockers under lock"]
  WRITE["Update enrolment pin + append audit event<br/>in one transaction"]
  REFRESH["Reload user and enrolment data"]
  OPEN --> PREVIEW --> CHECK
  CHECK -->|"Blocked"| BLOCK
  CHECK -->|"Allowed"| CONFIRM --> LOCK --> RECHECK
  RECHECK -->|"Changed or blocked"| BLOCK
  RECHECK -->|"Still allowed"| WRITE --> REFRESH
```

The same learner lock guards new practice sessions and lesson-progress starts.
A course update cannot silently replace an active session or remap progress from
changed/removed lessons. Same or older target revisions are rejected. Compatible
existing lesson evidence stays in place; incompatible evidence needs a separately
reviewed migration design. There is no force-reset button.

## 9. Administrator surface and access

| Page | content_admin | academic_admin | Purpose |
| --- | --- | --- | --- |
| `/admin` | Yes | Yes | Aggregate learning metrics |
| `/admin/students` | Yes | Yes | Search/paginate student summaries |
| `/admin/students/<id>` | Yes | Yes | Individual lesson and attempt aggregates |
| `/admin/questions` | Yes | Yes | Filter question performance by outcome/difficulty |
| `/admin/content` | Yes | Yes | Safe preview and review; lifecycle requests require academic role |
| `/admin/invitations` | Yes | Yes | Create/list/revoke beta invitations |
| `/admin/audit` | Yes | Yes | Latest 100 operational audit events |
| `/admin/users` | No | Yes | All profiles including admins, role changes, course migration |
| `/admin/operations` | No | Yes | Live release/database/content status |

The backend independently enforces the same restrictions. Hiding a link is only
presentation. Role changes require explicit confirmation; self-role changes and
removing the last academic administrator are rejected. Role changes are serialized
to protect the last-admin check. Analytics excludes raw submitted answers, auth
tokens and invitation secrets. Invitation plaintext is returned once on creation.

This dashboard is usable as the placeholder admin interface. It does not include
an in-browser content editor, video uploader, billing console, full log browser, metrics history
or unrestricted audit export.

## 10. Deployment and observability

```mermaid
flowchart LR
  BRANCH["Feature branch / PR"] --> CI["Lint · Types · Unit tests<br/>Fresh PostgreSQL · Integration tests<br/>Authenticated Chromium journeys<br/>Contract generation · Web build"]
  CI --> MAIN["Reviewed main branch"]
  MAIN --> STAGING["Automatic staging workflow<br/>Isolated Supabase + Railway"]
  STAGING --> STAGINGSMOKE["Preview environment · Google provider<br/>Auth gate · readiness · scheduled checks"]
  STAGINGSMOKE --> RELEASE["Manual production workflow<br/>Protected environment"]
  RELEASE --> MIGRATE["Migration safety + Supabase migrations"]
  MIGRATE --> APPROVAL["Human approval release gate"]
  APPROVAL --> IMPORT["Immutable question and course imports"]
  IMPORT --> API["Deploy API with release SHA"]
  API --> READY["Readiness + expected release smoke check"]
  READY --> WEB["Deploy web"]
  WEB --> SMOKE["Full application smoke check"]
  SMOKE --> LIVE["Production"]
  LIVE --> MONITOR["Scheduled availability check"]
  LIVE --> LOGS["Structured logs<br/>Request ID · Status · Duration · Release"]
  LIVE --> STATUS["Academic admin system status"]
```

Additive schema changes precede code rollout. Health-gated hosting overlap/draining
must be configured on the actual platform; source files alone do not prove those
settings are active. Roll application code back to a known-good compatible release
if needed; leave additive DB schema in place and repair forward. Test old-session
compatibility before changes to question revisions. No architecture can promise
zero disruption without testing those operational settings.

`/health` checks process liveness; `/ready` checks the database/schema and imported
content. Admin operations show current status, not historical uptime. Request IDs
connect user-visible failures to logs. See
[Deployment automation and observability](DEPLOYMENT_AUTOMATION_OBSERVABILITY.md)
for production environment setup and rollback procedures. The hosted pre-production path is in [Hosted staging deployment](HOSTED_STAGING.md). The browser-test boundary and local/CI runbook are in [Authenticated beta end-to-end verification](AUTHENTICATED_BETA_E2E.md).

## 11. Future extensions without blocking this beta milestone

```mermaid
flowchart LR
  CURRENT["Stable API contracts and learner identity"]
  CURRENT -.-> TUTOR["Tutor module<br/>Question-grounded context · Answer-lock rules<br/>Conversation persistence · Limits and cost budgets"]
  TUTOR -.-> MODEL["Selected local or hosted LLM"]
  CURRENT -.-> MEDIA["Video asset metadata<br/>Captions · Transcript · Playback"]
  MEDIA -.-> STORAGE["Chosen media host / object storage"]
  CURRENT -.-> HIST["Historical catalogue loader<br/>Version-aware question serving"]
  CURRENT -.-> EVENTS["Durable jobs / analytics pipeline<br/>Only when required by load"]
  OCR["Existing OCR staging"] -.-> INGEST["Reviewed ingestion adapter"]
  INGEST -.-> BANK["Validated authored question revisions"]
```

The friend's frontend can replace layout/components while retaining the same
`/api/v1` contracts, server-side session handling, KaTeX content blocks and error
envelopes. Public content rendering must not expose answer specifications.
Do not embed database access or admin authorization decisions into Figma-generated
client code.

## 12. Source map

- [Web app](../../apps/web/src/app), [admin UI](../../apps/web/src/components/admin-dashboard.tsx)
- [API routers](../../services/learning_api/src/learning_api/routers)
- [API contracts](../../services/learning_api/openapi.json),
  [generated TypeScript](../../apps/web/src/lib/api/schema.d.ts)
- [Shared checking](../../question_bank/src/question_bank/checking.py)
- [Question importer](../../question_bank/src/question_bank/repository.py),
  [course importer](../../question_bank/src/question_bank/course_repository.py)
- [Database migrations](../../supabase/migrations)
- [Content check](../../services/learning_api/src/learning_api/content_sync.py), [content review](../../services/learning_api/src/learning_api/content_review.py),
  [release gate](../../services/learning_api/scripts/verify_content_release.py),
  [bootstrap](../../services/learning_api/scripts/bootstrap_local.py)
- [Curriculum update](../../services/learning_api/src/learning_api/curriculum_admin.py)
- [CI](../../.github/workflows/ci.yml), [release](../../.github/workflows/deploy-production.yml)
