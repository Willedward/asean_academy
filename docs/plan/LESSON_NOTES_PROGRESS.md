# Lesson notes and explicit section progress

**Branch:** `feature/lesson-notes-progress`  
**Course snapshot:** `g3-sec1-math` revision 2  
**Lesson snapshot:** `n1-lesson-01` revision 2  
**Status:** Technical implementation complete; Mathematics/editorial review pending

## Delivered learner flow

The Lesson 1 route now combines the future video area and the written lesson on one
page. The video area remains an honest placeholder until a host, captions and a
transcript are supplied. Students can use the written draft in development preview
without waiting for the video.

The written lesson contains:

1. prime and composite number theory;
2. a worked primality test for 91 and 97;
3. prime-factorisation and index-notation theory;
4. a fully worked factorisation of 360;
5. a server-checked factorisation of 84;
6. common mistakes; and
7. a lesson summary.

The browser renders the existing safe text, inline-math and display-math blocks with
KaTeX. Worked solutions keep their authored step order. The active-recall response
and feedback are removed from the lesson payload and remain server-side until the
learner submits an answer.

## Progress semantics

Section completion is engagement evidence and never grants proficiency or mastery.

- Explanation, worked-example and summary sections require an explicit learner
  action. Scrolling alone records nothing.
- Active recall completes only after the deterministic checker accepts the answer.
- Learners can mark reading sections incomplete again.
- Completion is pinned to the exact immutable lesson revision. A new revision starts
  with independent section-completion records.
- Practice proficiency and checkpoint mastery retain their existing rules.

The API endpoints are:

```text
GET  /api/v1/lessons/{lesson_key}/section-progress
PUT  /api/v1/lessons/{lesson_key}/sections/{section_key}/completion
POST /api/v1/lessons/{lesson_key}/sections/{section_key}/active-recall
```

## Storage and authorization

Local development uses `learner_lesson_section_progress` in the existing SQLite
progress database. Hosted environments use the additive Supabase migration
`202609270008_lesson_section_progress.sql`.

The PostgreSQL record references `auth.users` and the exact `lesson_sections` row.
Row-level security permits authenticated learners to read only their own records.
All mutations continue through the authenticated Learning API, which verifies the
lesson, revision, section and prerequisite state.

## Release ordering

The new lesson revision must exist in PostgreSQL before the new API receives traffic.
The production workflow therefore performs these steps:

1. apply Supabase migrations;
2. import the validated immutable question revisions;
3. import course revision 2 and Lesson 1 revision 2;
4. deploy and smoke-test the API; and
5. deploy and smoke-test the web application.

The protected GitHub production environment now needs `PRODUCTION_DATABASE_URL` in
addition to the existing Supabase and Railway secrets.

## Content gate

Lesson 1 remains `draft`. The draft note is intentionally visible only when draft
preview is enabled. Before publication, a named Mathematics reviewer and editorial
reviewer must verify:

- definitions and mathematical statements;
- every calculation and worked step;
- age-appropriate wording;
- estimated lesson duration;
- KaTeX rendering on desktop and mobile; and
- agreement between the note, active-recall check and allocated practice questions.

The video still requires a hosting decision, captions and a transcript. None of those
items block technical testing of the written lesson.
