# Public marketing site template and product handoff

**Status:** reviewable template  
**Preview route:** `/marketing-preview`  
**Implementation branch:** `feature/marketing-site-template`

## Purpose

The promotional site and learning product should run as one coherent web experience.
The public pages explain the product and establish trust; the existing application owns
authentication, onboarding, learning, practice and progress. The first template is
deliberately isolated from the current `/` invitation landing page so a designer can
change its visual language without disrupting beta learners.

## Recommended route model

| Route                | Responsibility                                          |
| -------------------- | ------------------------------------------------------- |
| `/`                  | Public marketing home after founder and design approval |
| `/login`             | Existing Google invitation sign-in                      |
| `/onboarding`        | Existing learner setup                                  |
| `/learn`             | Authenticated Mathematics learning home                 |
| `/english`           | Authenticated English learning home                     |
| `/diagnostics`       | Authenticated readiness and diagnostic flow             |
| `/progress`          | Authenticated academic progress                         |
| `/marketing-preview` | Temporary review route for this template                |

Keeping these routes on the same origin avoids a second account system, duplicated
navigation logic and cross-domain authentication problems. Marketing calls to action
link to `/login?next=%2Flearn`; the existing sign-in callback validates the invitation
and returns the learner to the product.

## Template content

The template includes:

- responsive public navigation and an accessible skip link;
- a hero statement and code-native product illustration using the existing hornbill;
- a factual learning-loop explanation;
- separate Mathematics and English sections;
- a four-step product journey;
- student and family trust language;
- an invitation-beta FAQ; and
- repeated handoffs to the existing sign-in route.

It avoids invented performance statistics, testimonials, school logos, prices and public
registration claims. Those components should be added only when evidence and product
decisions exist.

## Designer handoff boundaries

The designer can replace layout, typography, artwork, motion and visual hierarchy inside
`apps/web/src/components/marketing/marketing-landing.tsx`. Preserve these product
contracts:

1. use the NextScholar name and approved brand assets;
2. keep the primary learner action linked to the existing sign-in route;
3. describe Layer 1 as Mathematics and English for ASEAN Scholarship preparation;
4. do not promise admission, score gains or access to confidential papers;
5. keep touch targets, keyboard focus, heading order and reduced-motion support; and
6. treat pricing, testimonials, public registration and school partnerships as content
   requiring explicit approval and evidence.

## Promotion to the public home

After visual and copy approval:

1. render `MarketingLanding` from `apps/web/src/app/page.tsx`;
2. retain the current invitation landing behind a server-side rollback flag for one
   deployment cycle;
3. add approved Open Graph artwork, canonical production URL and analytics consent;
4. test `/` → `/login` → callback → `/learn` on phone and desktop;
5. confirm the unauthenticated application routes continue to redirect safely; and
6. deploy the same Git revision for the public shell and authenticated application.

No marketing-specific backend, database table or paid API call is required for this
template.
