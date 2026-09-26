# Release operations without avoidable user disruption

## Objective

Normal releases should preserve signed-in sessions, in-progress practice and
stored progress. Supabase owns authentication and PostgreSQL state, so replacing
an application instance does not remove either. Releases still need compatible
API and database changes because a rolling deployment can briefly run old and
new application versions at the same time.

## Normal release sequence

1. Create a feature branch and run backend tests, frontend checks and migration
   validation in CI.
2. Take or confirm a recent managed database backup before a schema change.
3. Apply an **expand** migration. Add nullable columns, tables, indexes or enum
   values without deleting or renaming fields used by the running application.
4. Verify `/api/v1/ready` against the upgraded database.
5. Deploy the backend. Keep API changes backward compatible with the currently
   deployed web client.
6. Wait for the new backend instance to pass the readiness check before routing
   user traffic to it.
7. Deploy the web application after the compatible backend is healthy.
8. Run an authenticated smoke journey: sign in, load the course map, resume or
   create practice, submit an idempotent attempt, and load progress.
9. Observe error rate, latency, database connections and failed onboarding for a
   defined release window.
10. Perform any destructive **contract** migration in a later release after no
    deployed code reads the old field.

## Compatibility rules

- Add API response fields before making clients require them.
- Accept the old and new request shape during a transition release.
- Do not rename or drop a database column in the same release that introduces
  its replacement.
- Create new immutable content revisions. Existing sessions remain pinned to
  their original question and course revisions.
- Preserve attempt idempotency keys across retries and deployments.
- Run large data backfills in bounded batches rather than inside application
  startup.
- Keep database credentials and migration credentials out of browser bundles.

## Health checks

- `/api/v1/health` is a liveness check: the Python process can respond.
- `/api/v1/ready` is a readiness check: the process can reach PostgreSQL and the
  required schema is present.

Configure the hosting platform to route traffic only after `/api/v1/ready`
returns `200`. A failing new instance should never replace the last healthy
instance.

## Rollback

If errors rise after deployment:

1. stop promotion of the new release;
2. redeploy the last known-good application commit;
3. leave additive database columns and indexes in place;
4. verify sign-in, course loading, practice submission and progress;
5. inspect request IDs and immutable audit records; and
6. repair the forward migration in a new release.

Avoid reversing a database migration after users may have written data in the
new format. Application rollback is normally safer because additive schema
changes remain compatible with the previous release.

## When maintenance mode is justified

A short announced maintenance window is appropriate for an unavoidable table
rewrite, destructive migration, identity-provider change or integrity repair.
Routine application and additive schema releases should use the rolling process
above.
