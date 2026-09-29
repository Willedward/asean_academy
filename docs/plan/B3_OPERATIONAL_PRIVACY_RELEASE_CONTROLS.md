# B3 operational privacy and release controls

**Implementation status:** Backend complete locally on `feature/b3-operational-privacy-controls`; hosted rehearsal remains required.

**Scope boundary:** This milestone changes PostgreSQL, the FastAPI Learning API, generated OpenAPI types, tests, restore coverage and operating procedures. It does not replace or restyle Next.js pages. The final React implementation belongs to B4 and should call the contracts documented here.

## 1. Account deletion contract

Only an `academic_admin` can delete a student. A `content_admin` or student receives `403`; an administrator cannot delete their own account through this workflow. The operation has two server-owned steps:

1. `POST /api/v1/admin/students/{learner_id}/deletion/preview` locks no data and returns the target email for explicit confirmation, category counts, retained categories, and a signed preview token valid for 15 minutes.
2. `POST /api/v1/admin/students/{learner_id}/deletion/execute` requires that token, the exact email after case normalization, and a reason of 10–500 characters.

Execution locks the learner and obtains an advisory transaction lock. It rejects an expired/tampered token, a changed data snapshot, a missing/non-student target, an email mismatch, or self-deletion. This prevents an administrator from approving one preview and deleting a different or subsequently changed account.

The transaction deletes the Supabase Auth user. Database foreign keys then remove the profile, enrolments, sessions, selected questions, attempts, question and lesson progress, mastery evidence, diagnostics, and question reports. The immutable learning triggers allow deletion only while the transaction-local deletion target matches that student. Normal updates and deletes remain rejected.

The transaction retains:

- one `account_deletion_records` row containing HMAC-SHA256 learner/email references, the administrator, reason, pre-deletion category counts, request ID and completion time;
- one immutable `account_deletion_completed` audit event with a pseudonymous learner reference; and
- any infrastructure backup copies until their configured expiry.

It does not retain the learner's raw email, profile, answers, report comment, diagnostic result, or Google identity in the deletion record. Foreign keys null the deleted learner's actor/target fields in older audit events while their event contents remain immutable.

### Operator procedure

1. Confirm the request through the team's approved support channel and record the reason. Never ask for a Google password, access token or database password.
2. Find the learner UUID through the protected administrator student view.
3. Call the preview endpoint and compare the returned email and counts with the request. Do not copy the preview token into chat, tickets or logs.
4. If the target is wrong or counts change, stop and create a new preview.
5. Execute with the preview token, confirmation email and reason.
6. Record the returned pseudonymous `target_reference`, completion time and API request ID in the support record. Do not add the deleted email to that record.
7. Confirm the learner no longer appears in the student list and that sign-in no longer restores an academy profile.
8. If the request fails, investigate by request ID. Do not bypass the endpoint with manual table deletes.

The B4 admin screen should render the preview counts, retained categories, token expiry and confirmation field, then require a second explicit action. It must never implement cascades or deletion rules in the browser.

## 2. Beta retention schedule

These are the operational defaults for the invitation-only, tutor-free Beta. They should be copied into the published privacy notice and reviewed before the first real cohort. Shorter legally required periods override this schedule; any longer period needs a recorded purpose and owner.

| Data | Working retention | End-of-period action | Owner |
| --- | --- | --- | --- |
| Active account, enrolment, attempts, progress, mastery and diagnostics | While enrolled; delete on a verified account-deletion request | Use the protected deletion workflow | Academic operations |
| Inactive Beta learner data without a deletion request | Cohort end plus 90 days | Notify if required, then run an approved cohort cleanup | Academic operations |
| Open question reports | Until resolved/dismissed | Retain with learner while active | Content operations |
| Resolved/dismissed question reports | 180 days after closure, unless the account is deleted first | Aggregate issue counts if needed, then delete the learner-linked row | Content operations |
| Immutable operational audit events | 365 days | Reviewed pseudonymisation/archive migration | Founder/operator |
| Account-deletion evidence | 365 days | Reviewed deletion migration; retain only aggregate counts afterward | Founder/operator |
| API security events | 180 days | Reviewed bounded cleanup | Founder/operator |
| Expired rate-limit counters | 7 days after window end | Scheduled bounded cleanup | Backend owner |
| Application logs | 30 days | Provider expiry | Founder/operator |
| Database backups | Provider setting, target 30 days for Beta | Automatic provider expiry; verify after configuration changes | Founder/operator |
| Local exports and restore-drill databases | Same working session only | Destroy immediately after validation | Person running drill |

No tutor conversation data exists in Beta. If the AI tutor is enabled later, it requires a separate message/usage retention decision before any real student data is sent to a provider.

Retention cleanup must run through a reviewed migration or maintenance command with a dry-run count, bounded batches, request/change reference and post-run verification. Do not weaken immutable triggers globally or expose service-role credentials to the web client.

## 3. Administrator operational evidence

The administrator overview now includes diagnostic sessions started, submitted and in progress; diagnostic resets; total/open/in-review/resolved/dismissed question reports; and rate-limit rejections in the previous 24 hours. These are aggregate counts. Detailed student records remain behind existing role checks.

Use them with request IDs and immutable audit history:

1. identify the affected route and request ID;
2. check `/api/v1/ready` and `/api/v1/admin/operations/status`;
3. compare report/diagnostic/security counts with the expected journey;
4. inspect the audit event without copying answers or credentials into support notes; and
5. rollback the application release when the error began with a deploy, leaving compatible additive schema in place.

## 4. Availability and incident ownership

During the controlled cohort, **William (founder/operator)** is the primary availability owner for the scheduled GitHub `Staging availability` and `Production availability` workflow results and Railway errors. A second named human must be added as backup before the first student invitation. GitHub notification delivery to both owners must be tested; a failed scheduled run is an incident signal, not proof of an outage.

Checks run every 30 minutes in staging and every 15 minutes in production. Before a public launch, add an independent external uptime monitor and provider error alert so GitHub itself is not the only observer.

Incident sequence:

1. acknowledge and save the failing workflow URL, release SHA, time and request IDs;
2. stop the next deployment and invitation batch;
3. check health, readiness, database reachability and recent migration status;
4. for a release regression, deploy the last known-good application SHA and keep additive migrations;
5. run public and authenticated smoke journeys;
6. restore only for confirmed data loss/corruption, into a separate database first; and
7. document impact, resolution and prevention without putting student answers or tokens in the incident record.

## 5. Restore and release rehearsal

`scripts/backup_restore_drill.py` verifies SHA-256 row signatures for 27 critical tables, including every diagnostic table, question reports and pseudonymous account-deletion records. The target must be an empty disposable database and must never be production or staging.

```bash
SOURCE_DATABASE_URL='postgresql://source' \
RESTORE_DATABASE_URL='postgresql://empty-disposable-target' \
uv run --project services/learning_api --locked \
  python scripts/backup_restore_drill.py
```

A successful result reports `status: passed`, the table count and per-table row counts. Destroy the restored database after validation.

For each Beta release candidate:

1. run migration safety checks and the full CI suite;
2. confirm a recent managed backup and its configured retention;
3. apply additive migrations before application deployment;
4. require readiness before traffic promotion;
5. run deployment smoke, manual Google sign-in, an authenticated read journey and one idempotent practice submission;
6. run the bounded staging load smoke and intentional rate-limit tests with test identities;
7. observe errors and latency for the release window; and
8. record the known-good SHA and rollback result.

Suggested bounded staging commands are in [API_ABUSE_RECOVERY.md](API_ABUSE_RECOVERY.md). Hosted evidence remains incomplete until real staging URLs, a short-lived tester token and alert recipients are configured; local tests cannot substitute for that external proof.

## 6. B3 acceptance record

Local acceptance requires:

- fresh migration chain through `202609290014`;
- PostgreSQL integration coverage for preview, confirmation, cascades and pseudonymous evidence;
- role/contract tests for both endpoints;
- report/diagnostic operational aggregates;
- successful 27-table backup/restore signature comparison;
- migration safety, Ruff, complete API/question-bank tests, generated contract verification, web lint/typecheck/tests and production build.

Hosted acceptance requires:

- Supabase backup retention recorded;
- staging migration and readiness pass;
- rate-limit rejection observed and diagnosable by request ID;
- bounded health and authenticated-read load smoke within the agreed threshold;
- primary and backup alert delivery tested; and
- one application rollback rehearsal from staging.

### Local evidence recorded 29 September 2026

- all 14 migrations applied from an empty PostgreSQL 16 database;
- 94 Learning API/deployment-smoke tests passed with PostgreSQL integrations enabled;
- 28 question-bank tests and Ruff passed;
- 30 web tests, ESLint, TypeScript and the Next.js production build passed;
- OpenAPI and TypeScript contracts regenerated successfully; and
- the final dump/restore drill matched content and signatures across all 27 critical tables.

This evidence proves the repository and disposable database workflow. It does not claim
that hosted alert delivery, Supabase backup retention, staging rate limits, real Google
OAuth, or rollback has been exercised. Those remain explicit B3 release gates.
