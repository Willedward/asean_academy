begin;

create table english_essay_feedback_usefulness_responses (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    submission_id uuid not null references english_essay_submissions(id) on delete restrict,
    feedback_source text not null check (
        feedback_source in ('development_fixture', 'validated_ai')
    ),
    provider_feedback_id uuid references english_essay_provider_feedback(id) on delete restrict,
    marking_feedback_id uuid references english_essay_marking_feedback(id) on delete restrict,
    rating text not null check (rating in ('helpful', 'partly_helpful', 'not_helpful')),
    note text check (note is null or length(note) <= 1000),
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    created_at timestamptz not null default now(),
    check (
        (feedback_source = 'validated_ai'
         and provider_feedback_id is not null
         and marking_feedback_id is null)
        or
        (feedback_source = 'development_fixture'
         and marking_feedback_id is not null
         and provider_feedback_id is null)
    ),
    unique (student_id, idempotency_key),
    unique (provider_feedback_id),
    unique (marking_feedback_id)
);

create index english_essay_feedback_usefulness_student_created_idx
    on english_essay_feedback_usefulness_responses(student_id, created_at desc);

create or replace function validate_english_essay_feedback_usefulness()
returns trigger
language plpgsql
as $$
declare
    provider_row english_essay_provider_feedback%rowtype;
    fixture_row english_essay_marking_feedback%rowtype;
begin
    if new.feedback_source = 'validated_ai' then
        select * into provider_row
          from english_essay_provider_feedback
         where id = new.provider_feedback_id;
        if provider_row.id is null
           or row(new.student_id, new.submission_id)
              is distinct from row(provider_row.student_id, provider_row.submission_id) then
            raise exception 'Essay usefulness response must match owned validated feedback';
        end if;
    else
        select * into fixture_row
          from english_essay_marking_feedback
         where id = new.marking_feedback_id;
        if fixture_row.id is null
           or row(new.student_id, new.submission_id)
              is distinct from row(fixture_row.student_id, fixture_row.submission_id) then
            raise exception 'Essay usefulness response must match owned fixture feedback';
        end if;
    end if;
    return new;
end;
$$;

create or replace function protect_english_essay_feedback_usefulness()
returns trigger
language plpgsql
as $$
begin
    raise exception 'Essay feedback usefulness responses are immutable';
end;
$$;

create trigger english_essay_feedback_usefulness_is_valid
before insert on english_essay_feedback_usefulness_responses
for each row execute function validate_english_essay_feedback_usefulness();

create trigger english_essay_feedback_usefulness_is_immutable
before update or delete on english_essay_feedback_usefulness_responses
for each row execute function protect_english_essay_feedback_usefulness();

alter table english_essay_feedback_usefulness_responses enable row level security;

create policy english_essay_feedback_usefulness_owner_read
on english_essay_feedback_usefulness_responses for select
using (student_id = auth.uid());

revoke all on english_essay_feedback_usefulness_responses from anon, authenticated;
grant select on english_essay_feedback_usefulness_responses to authenticated;
grant all on english_essay_feedback_usefulness_responses to service_role;

comment on table english_essay_feedback_usefulness_responses is
    'One immutable learner usefulness response per exact essay feedback record; no provider usage or cost is exposed.';

commit;
