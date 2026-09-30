begin;

alter table math_question_banks
    add column if not exists bank_role text not null default 'learning';

alter table math_question_banks
    add constraint math_question_banks_bank_role_check
    check (bank_role in ('learning', 'diagnostic'));

create index if not exists math_question_banks_role_topic_idx
    on math_question_banks (bank_role, school_level, topic_id, status);

commit;
