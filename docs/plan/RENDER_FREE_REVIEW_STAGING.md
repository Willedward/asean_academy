# Free shared question-review staging

**Implementation:** 2 October 2026 on
`feature/bulk-question-authoring-pipeline`.

## Purpose

This environment lets two or more trusted reviewers use the protected
`/admin/content` dashboard while the Secondary 1–2 question bank is being built. It
does not require lesson videos, payment integration or a production launch.

The repository root contains `render.yaml`, which defines two Singapore-region Render
Free web services:

- `nextscholar-review-api` runs FastAPI, applies reviewed migrations and imports
  immutable authored content before each deployment;
- `nextscholar-review-web` runs Next.js and sends authenticated server requests to the
  API; and
- a separate Supabase staging project stores Auth users, roles, append-only review
  decisions and other durable state.

Render's local filesystem is not used for durable data. Authored question JSON stays in
Git, and review decisions stay in Supabase.

## First deployment

### 1. Create the isolated Supabase project

Create a staging project in Singapore. It must be separate from any future production
project. Collect these values from the staging project:

| Render prompt                | Supabase value                                                                |
| ---------------------------- | ----------------------------------------------------------------------------- |
| `ASEAN_ACADEMY_DATABASE_URL` | Transaction-pooler PostgreSQL URL with its password                           |
| `SUPABASE_URL`               | Project URL, such as `https://PROJECT_REF.supabase.co`                        |
| `SUPABASE_ANON_KEY`          | Public publishable key; use the legacy anon key only for a legacy JWT project |

Keep the database URL private. The Supabase URL and publishable key are intentionally
exposed to the browser, but a service-role key must never be used here.

### 2. Create the Render Blueprint

1. Sign in to Render and choose **New > Blueprint**.
2. Connect the GitHub repository that contains this file.
3. Select `feature/bulk-question-authoring-pipeline` as the Blueprint branch.
4. Leave the Blueprint path as `render.yaml`.
5. Enter the three Supabase values when Render prompts for variables marked
   `sync: false`.
6. Apply the Blueprint and wait for both services to report healthy.

Render generates the abuse-protection secret. The Blueprint passes each service's
public URL and the public Supabase values between services, so they do not need to be
copied again.

The API's final build step refuses to run outside `ASEAN_ACADEMY_ENV=preview`. It takes
an advisory database lock, checks migration safety, applies only pending migrations,
imports the validated course and question content, and verifies the result. Repeating
the same deploy is safe. Render reserves its dedicated pre-deploy command for paid web
services, so the free staging blueprint performs this guarded operation at the end of
the build instead.

### 3. Configure hosted Google sign-in

After Render assigns the web URL, configure the exact URL in both systems.

In Google Auth Platform:

| Setting                      | Value                                              |
| ---------------------------- | -------------------------------------------------- |
| Authorized JavaScript origin | `https://YOUR_WEB_SERVICE.onrender.com`            |
| Authorized redirect URI      | `https://PROJECT_REF.supabase.co/auth/v1/callback` |

In Supabase **Authentication > URL Configuration**:

| Setting      | Value                                                 |
| ------------ | ----------------------------------------------------- |
| Site URL     | `https://YOUR_WEB_SERVICE.onrender.com`               |
| Redirect URL | `https://YOUR_WEB_SERVICE.onrender.com/auth/callback` |

Enable the Google provider and allow new users. Application invitations still prevent
uninvited users from entering the beta after authentication.

### 4. Create reviewer accounts

Create an invitation for each reviewer from a trusted local terminal. Do not paste the
database URL or invitation code into chat.

```bash
read -r -s -p "Staging database URL: " DATABASE_URL
echo
export DATABASE_URL
uv run --project services/learning_api --locked \
  python services/learning_api/scripts/create_invitation.py reviewer@example.com
unset DATABASE_URL
```

After that reviewer accepts the invitation, assign the appropriate role:

```bash
read -r -s -p "Staging database URL: " DATABASE_URL
echo
export DATABASE_URL
uv run --project services/learning_api --locked \
  python services/learning_api/scripts/set_admin_role.py \
  reviewer@example.com --role academic_admin
unset DATABASE_URL
```

Use `academic_admin` for a reviewer who may make Mathematics and editorial decisions.
Use `content_admin` for an editorial-only reviewer. Sign out and back in after a role
change, then open `/admin/content`.

## Recurring question-batch deployment

A draft question should not deploy by itself. Deploy a complete controlled batch of
20–30 questions through this path:

1. claim the planned batch on a small claim branch;
2. generate or author only the allocated stable question keys;
3. validate schema, answers, hints, worked solutions, difficulty distribution and
   cross-bank duplicates;
4. open a pull request into `feature/bulk-question-authoring-pipeline`;
5. merge only after CI and ownership checks pass;
6. Render deploys the passing merge automatically;
7. the API build imports that exact Git revision into Supabase before starting the new
   service revision; and
8. reviewers select the batch in `/admin/content` and record decisions.

Review decisions are append-only and tied to a content fingerprint. Correcting a
question in Git creates a new fingerprint, so approval for the old text cannot silently
approve the changed question.

## Verification after the first deployment

1. Open the web URL. A sleeping free service can take about one minute to wake.
2. Sign in with an invited Google account.
3. Confirm the reviewer can open `/admin/content` and select an authored batch.
4. Record one review decision and refresh the page to prove it persists.
5. Confirm `/api/v1/ready` on the API URL reports `environment: preview` and the expected
   release SHA.
6. Merge a harmless validated content update and confirm Render waits for GitHub CI,
   then deploys the merge commit.

## Free-tier boundary

Render Free web services spin down after 15 minutes without inbound traffic and may
take about one minute to wake. Two services share the workspace's monthly free instance
hours. This is suitable for intermittent internal review, but move to the existing
Railway staging path before daily beta use or when predictable response time matters.
