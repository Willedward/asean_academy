begin;

alter type session_question_status add value if not exists 'incorrect';

alter table session_questions
    drop constraint session_questions_selection_reason_check;
alter table session_questions
    add constraint session_questions_selection_reason_check check (
        selection_reason in (
            'required_retry', 'unseen', 'least_recently_attempted',
            'configured_lesson_pool', 'configured_checkpoint_pool'
        )
    );

alter table practice_sessions
    add constraint practice_sessions_learning_scope_check check (
        (
            scope->>'mode' in ('guided_practice', 'retry_review')
            and nullif(scope->>'lesson_key', '') is not null
            and not (scope ? 'unit_key')
        )
        or (
            scope->>'mode' = 'checkpoint'
            and nullif(scope->>'unit_key', '') is not null
            and not (scope ? 'lesson_key')
        )
    ) not valid;

create unique index practice_sessions_one_active_checkpoint_idx
    on practice_sessions(student_id, (scope->>'unit_key'))
    where status = 'active' and scope->>'mode' = 'checkpoint';

comment on constraint practice_sessions_learning_scope_check on practice_sessions is
    'New learning sessions target either one lesson or one unit checkpoint. Kept NOT VALID so historical pre-contract sessions do not block deployment.';

commit;
