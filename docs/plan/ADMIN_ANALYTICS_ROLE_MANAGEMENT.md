# Backend admin analytics and role management

## Status

This backend milestone is implemented without depending on lesson videos or a
finished administrator frontend. It extends the existing protected invitation
workspace with student progress, aggregate learning analytics, question
performance and academic-administrator-only role management.

The browser never receives database credentials. Every endpoint first verifies
the Supabase access token and then reads the administrator role from PostgreSQL.

## Roles

| Role | Learning access | Invitations and analytics | Role changes |
| --- | --- | --- | --- |
| `student` | Enrolled courses only | No | No |
| `content_admin` | If separately enrolled | Yes | No |
| `academic_admin` | If separately enrolled | Yes | Yes |

Role assignment is stored in `profiles.role`. The backend does not trust a role
sent by the browser or an old token. Academic administrators cannot change their
own role, and the last academic administrator cannot be demoted.

For the first administrator, the Google account must sign in and accept an
invitation once so its verified email is copied to `profiles.email`. A trusted
operator can then run:

```bash
set -a
source .env.hosted.local
set +a
uv run --project services/learning_api --locked \
  python services/learning_api/scripts/set_admin_role.py \
  administrator@example.com --role academic_admin
```

After that bootstrap, normal role changes use the protected API and every real
change writes an immutable `role_changed` audit event.

## API

All paths require a database-backed `content_admin` or `academic_admin` role,
except role changes, which require `academic_admin`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/admin/students` | Paginated, searchable student summaries |
| `GET` | `/api/v1/admin/students/{learnerId}` | Lesson and difficulty progress for one student |
| `GET` | `/api/v1/admin/analytics/overview` | Aggregate engagement, mastery and attempt metrics |
| `GET` | `/api/v1/admin/analytics/questions` | Question accuracy, hints, give-ups and retry demand |
| `PATCH` | `/api/v1/admin/users/{learnerId}/role` | Academic-admin-only role change |

Student analytics deliberately exclude submitted answer bodies, access tokens,
invitation codes and worked solutions. Question analytics expose aggregate
counts only.

## Database migration

`202609260007_admin_analytics_roles.sql` is an additive migration. It:

- adds normalized verified email to `profiles`;
- backfills existing profiles from Supabase Auth;
- adds the `role_changed` audit type; and
- adds indexes used by student and question analytics.

The migration must be applied before deploying API code that reads
`profiles.email`. Existing application versions continue to work after the
migration, enabling a migration-first rolling release.

## Verification

```bash
uv run --project services/learning_api --locked \
  pytest services/learning_api/tests
uv run --project services/learning_api --locked \
  ruff check services/learning_api/src services/learning_api/tests \
  services/learning_api/scripts
```

Hosted verification should cover:

1. a student receives `403 administrator_required`;
2. a content administrator can read analytics but receives
   `403 academic_administrator_required` for role changes;
3. an academic administrator can change another user's role;
4. the audit trail records the old and new role without storing personal
   credentials; and
5. student and question analytics return aggregates without submitted answers.
