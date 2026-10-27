begin;

alter type english_lesson_progress_state add value if not exists 'mastered';

alter table english_session_questions
    add column correct_parts smallint not null default 0 check (correct_parts >= 0),
    add column total_parts smallint not null default 0 check (total_parts >= 0),
    add column hint_used boolean not null default false,
    add column hint_revealed_at timestamptz,
    add column retry_source_question_id uuid
        references english_objective_questions(id) on delete restrict,
    add constraint english_session_question_part_score_valid
        check (correct_parts <= total_parts),
    add constraint english_session_question_hint_time_valid
        check ((not hint_used and hint_revealed_at is null) or hint_used);

alter table english_practice_sessions
    add column exam_profile_key text not null
        default 'asean-english-sec1-id-reported-v1'
        check (exam_profile_key ~ '^asean-english-[a-z0-9-]+-v[0-9]+$');

comment on column english_session_questions.correct_parts is
    'Deterministic correct-part count used with total_parts for the 75 percent proficiency rule.';
comment on column english_session_questions.hint_used is
    'Persisted before a hint is returned; hinted qualifying work cannot grant proficiency.';
comment on column english_session_questions.retry_source_question_id is
    'Original failed exit ticket addressed by a distinct retry-review parallel form.';
comment on column english_practice_sessions.exam_profile_key is
    'Versioned exam profile pinned when the session is assigned for historical interpretation.';

commit;
