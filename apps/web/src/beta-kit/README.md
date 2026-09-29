# NextScholar beta kit

The beta frontend design, as React components, ready to wire to the learning API.
The source frontend-kit commit was additive and left existing pages unchanged. The B3 integration branch also adds a tested request-level production guard in `src/proxy.ts`; existing application routes continue to use their current implementations.

## See it

```bash
corepack pnpm dev:web
# open http://localhost:3000/beta-kit
```

The index lists all 69 screen states. Each one opens full screen (resize the window: one
component covers phone and desktop), and "Phone and desktop" shows both side by side.
The preview is switched off in production builds unless `NEXT_PUBLIC_BETA_KIT=true`.

## How it is built

| Folder | What is in it |
|---|---|
| `screens/` | One component per screen, e.g. `DashboardScreen`, `PracticeQuestionScreen`. Each takes plain data as props and never fetches. |
| `types.ts` | Shared view models (`Player`, `Quest`, `League`, `LessonSummary`, `UnitSummary`...). Each screen file adds its own `XxxProps`. |
| `adapters.ts` | Maps today's API responses (course map, progress, next action) to the view models. Tested in `adapters.test.ts`. |
| `components/` | Building blocks: buttons, cards, the hornbill mascot (SVG, 6 moods, 5 outfits), XP chips, level ring, quests, streak, medals, confetti, answer feedback. |
| `shell/` | `AppShell` (tab screens: bottom nav on phones, sidebar on desktop), `FocusShell` (lesson, practice, checkpoint, essay), `BareShell` (landing, sign in, errors). |
| `sample-data.ts`, `preview/` | Sample student "Dimas" and the preview registry. Not needed in production. |
| `theme.css` | Brand tokens as Tailwind v4 theme values (`bg-ns-ink`, `text-ns-muted`, `animate-ns-pop`...). |
| `HANDOFF.md` | Screen by screen: which data exists in the API today and which is new backend work. |

Every screen file has a `/** Canvas: ... */` comment naming the boards on the design canvas
it implements, and props carry `// API: ...` or `// NEW` comments.

## Using a screen in a real page

1. Add one line to `src/app/globals.css`, right after `@import "tailwindcss";`:

   ```css
   @import "../beta-kit/theme.css";
   ```

   It only adds `ns-` prefixed tokens, so current pages do not change. For the brand font, load
   `src/beta-kit/fonts/Figtree-latin-wght.woff2` with `next/font/local` as `--font-figtree`
   (see `src/app/beta-kit/layout.tsx`).

2. In the page (a server component), load data, map it, render the screen:

   ```tsx
   import { unitFromCourseMap } from "@/beta-kit/adapters";
   import { UnitScreen } from "@/beta-kit/screens/learn";

   export default async function CoursePage({ params }: { params: Promise<{ courseKey: string }> }) {
     const { courseKey } = await params;
     const [course, progress] = await Promise.all([getCourseMap(courseKey), getProgress()]);
     const player = await getPlayer(); // NEW endpoint, see HANDOFF.md
     const unit = unitFromCourseMap(course, 0, progress);
     if (!unit) notFound();
     return <UnitScreen player={player} unit={unit} courseTitle={course.title} timeLabel="About 3.5 hours" legend="stars" routes={ROUTES} />;
   }
   ```

3. Links: screens read hrefs from their props, and nav and chip links from a `routes` object
   (`routes.ts`, type `KitRoutes`). Make one `ROUTES` constant with your real paths and pass it
   everywhere.

4. Interactivity: screens are server-safe and stateless. The current state (wrong answer,
   hint open, dialog open) is a prop. Forms post with plain `<form action>` (a URL or a
   server action); input names are listed in `HANDOFF.md`. For things that need client state
   (choice buttons, rating, toggles saving on change, video controls), wrap the screen in a
   small `"use client"` component. `practice-player.tsx` can keep its state machine and render
   `PracticeQuestionScreen` for each state.

5. Rich content (question stems, lesson sections, hints, solutions) goes in as `ReactNode`
   slots, so pass your existing `<MathContent />`.

## Checks

```bash
corepack pnpm lint && corepack pnpm typecheck && corepack pnpm test:web && corepack pnpm build
```

All pass on this branch. Motion is off when the device asks for reduced motion.
