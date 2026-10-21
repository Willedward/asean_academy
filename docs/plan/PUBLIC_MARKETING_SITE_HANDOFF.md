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
| `/register`          | Stable entry point for invitation, waitlist or signup   |
| `/login`             | Existing Google invitation sign-in                      |
| `/onboarding`        | Existing learner setup                                  |
| `/learn`             | Authenticated Mathematics learning home                 |
| `/english`           | Authenticated English learning home                     |
| `/diagnostics`       | Authenticated readiness and diagnostic flow             |
| `/progress`          | Authenticated academic progress                         |
| `/marketing-preview` | Temporary review route for this template                |

Keeping these routes on the same origin avoids a second account system, duplicated
navigation logic and cross-domain authentication problems. Marketing registration
calls to action link to `/register`. In the private beta, that page sends invited
students to `/login?next=%2Flearn`; the existing sign-in callback validates the
invitation and returns the learner to the product.

`/register` is the stable seam between promotion and access. When access policy changes,
the implementation behind that route can become a verified waitlist or public signup
without changing links across the marketing site, campaigns or QR codes.

## Template content

The template includes:

- responsive public navigation and an accessible skip link;
- a hero statement and code-native product illustration using the existing hornbill;
- a factual learning-loop explanation;
- separate Mathematics and English sections;
- a four-step product journey;
- student and family trust language;
- a testimonial section with clearly labelled evidence placeholders;
- an invitation-beta FAQ; and
- repeated handoffs to the registration entry route.

It avoids invented performance statistics, testimonial quotes, school logos, prices and
public registration claims. The testimonial cards are layout slots, not endorsements.
Real content should be added only when evidence, consent and product decisions exist.

## Designer handoff boundaries

The designer can replace layout, typography, artwork, motion and visual hierarchy inside
`apps/web/src/components/marketing/marketing-landing.tsx`. Preserve these product
contracts:

1. use the NextScholar name and approved brand assets;
2. keep the primary learner action linked to `/register` and the separate sign-in action
   linked to the existing authentication route;
3. describe Layer 1 as Mathematics and English for ASEAN Scholarship preparation;
4. do not promise admission, score gains or access to confidential papers;
5. keep touch targets, keyboard focus, heading order and reduced-motion support; and
6. treat pricing, testimonials, public registration and school partnerships as content
   requiring explicit approval and evidence.

## Registration states

The same `/register` route can support three product stages:

1. **Invitation-only beta (current):** explain the access boundary and direct invited
   students to Google sign-in. Do not collect an email or imply that an account exists.
2. **Waitlist:** collect only the approved fields, validate on the server, rate-limit
   submissions, record consent and display a truthful confirmation state.
3. **Public registration:** start the approved identity flow and return the learner to
   onboarding. Authentication and learner records remain owned by the application.

If a waitlist is approved, the minimum data contract should be email, country,
student/parent role, consent timestamp and campaign source. Add a privacy notice,
retention decision, duplicate handling and abuse protection before enabling collection.

## Testimonial publication contract

Each published testimonial needs:

- the exact approved quote;
- the public attribution or approved anonymous label;
- the speaker's role, such as student or parent;
- recorded publication consent and approval status; and
- evidence and context for any measurable outcome claim.

The public page should render approved entries only. Withdrawal of consent must remove
the testimonial without requiring a marketing redesign.

## Promotion to the public home

After visual and copy approval:

1. render `MarketingLanding` from `apps/web/src/app/page.tsx`;
2. retain the current invitation landing behind a server-side rollback flag for one
   deployment cycle;
3. add approved Open Graph artwork, canonical production URL and analytics consent;
4. change the registration page's back links from `/marketing-preview` to `/`;
5. test `/` → `/register` → `/login` → callback → `/learn` on phone and desktop;
6. confirm the unauthenticated application routes continue to redirect safely; and
7. deploy the same Git revision for the public shell and authenticated application.

No marketing-specific backend, database table or paid API call is required for this
template.
