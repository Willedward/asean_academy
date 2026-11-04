begin;

-- Full mocks reuse the protected diagnostic session tables. Each form has its own purpose,
-- so a learner keeps one session per mock.
alter type english_diagnostic_purpose add value 'mock_a';
alter type english_diagnostic_purpose add value 'mock_b';

alter table english_diagnostic_sessions
    drop constraint english_diagnostic_sessions_form_key_check;

alter table english_diagnostic_sessions
    add constraint english_diagnostic_sessions_form_key_check check (
        form_key ~ '^english-(baseline|endline|mock)-[a-z0-9-]+-v[0-9]+$'
    );

commit;
