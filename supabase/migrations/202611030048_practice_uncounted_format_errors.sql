begin;

alter table session_questions
    add column uncounted_format_errors integer not null default 0
        check (uncounted_format_errors >= 0);

comment on column session_questions.uncounted_format_errors is
    'Unreadable submissions since the last counted attempt. Past the limit, the next one counts as an incorrect attempt, so a learner cannot be stuck on a question.';

commit;
