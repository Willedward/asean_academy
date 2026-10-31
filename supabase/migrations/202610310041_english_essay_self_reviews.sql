begin;

create table english_essay_self_reviews (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    submission_id uuid not null unique
        references english_essay_submissions(id) on delete restrict,
    rubric_version_id uuid not null
        references english_essay_rubric_versions(id) on delete restrict,
    criterion_reflections jsonb not null check (
        jsonb_typeof(criterion_reflections) = 'array'
        and jsonb_array_length(criterion_reflections) between 3 and 6
    ),
    overall_reflection text not null check (
        length(btrim(overall_reflection)) between 1 and 2000
    ),
    disclaimer_acknowledged boolean not null check (disclaimer_acknowledged),
    completed_at timestamptz not null default now()
);

create table english_essay_self_review_idempotency_keys (
    student_id uuid not null references auth.users(id) on delete cascade,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    self_review_id uuid not null
        references english_essay_self_reviews(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (student_id, idempotency_key)
);

create index english_essay_self_reviews_student_completed_idx
    on english_essay_self_reviews(student_id, completed_at desc);

create or replace function validate_english_essay_self_review()
returns trigger
language plpgsql
as $$
declare
    source_submission english_essay_submissions%rowtype;
    source_rubric english_essay_rubric_versions%rowtype;
    submitted_keys text[];
    rubric_keys text[];
begin
    select * into source_submission
      from english_essay_submissions
     where id = new.submission_id
     for update;
    if not found then
        raise exception 'English essay self-review submission does not exist';
    end if;

    select * into source_rubric
      from english_essay_rubric_versions
     where id = source_submission.rubric_version_id;

    if row(new.student_id, new.rubric_version_id)
       is distinct from row(source_submission.student_id, source_submission.rubric_version_id) then
        raise exception 'English essay self-review must use the owned submission and pinned rubric revision';
    end if;

    if exists (
        select 1
          from jsonb_array_elements(new.criterion_reflections) reflection
         where jsonb_typeof(reflection) <> 'object'
            or coalesce(reflection->>'criterion_key', '') = ''
            or case
                when coalesce((reflection->>'selected_band_level') ~ '^[0-9]+$', false)
                then (reflection->>'selected_band_level')::integer
                    not between source_rubric.scale_min and source_rubric.scale_max
                else true
               end
            or length(btrim(coalesce(reflection->>'evidence_note', ''))) not between 1 and 1000
            or length(btrim(coalesce(reflection->>'improvement_action', ''))) not between 1 and 1000
    ) then
        raise exception 'English essay self-review criterion reflection is invalid';
    end if;

    select array_agg(reflection->>'criterion_key' order by reflection->>'criterion_key')
      into submitted_keys
      from jsonb_array_elements(new.criterion_reflections) reflection;
    select array_agg(criterion->>'criterion_key' order by criterion->>'criterion_key')
      into rubric_keys
      from jsonb_array_elements(source_rubric.criteria) criterion;

    if submitted_keys is distinct from rubric_keys then
        raise exception 'English essay self-review must cover every pinned rubric criterion exactly once';
    end if;
    return new;
end;
$$;

create or replace function protect_english_essay_self_review()
returns trigger
language plpgsql
as $$
begin
    raise exception 'English essay self-reviews are immutable';
end;
$$;

create trigger english_essay_self_review_is_complete
before insert on english_essay_self_reviews
for each row execute function validate_english_essay_self_review();

create trigger english_essay_self_review_is_immutable
before update or delete on english_essay_self_reviews
for each row execute function protect_english_essay_self_review();

alter table english_essay_self_reviews enable row level security;
alter table english_essay_self_review_idempotency_keys enable row level security;

create policy english_essay_self_reviews_owner_read
on english_essay_self_reviews for select using (student_id = auth.uid());

create policy english_essay_self_review_idempotency_owner_read
on english_essay_self_review_idempotency_keys for select using (student_id = auth.uid());

grant select on english_essay_self_reviews to authenticated;
grant select on english_essay_self_review_idempotency_keys to authenticated;

comment on table english_essay_self_reviews is
    'Immutable learner-owned reflections against the exact instructional rubric pinned to an essay submission. These are not marks or AI feedback.';
comment on column english_essay_self_reviews.criterion_reflections is
    'One learner-selected descriptor, evidence note and improvement action per pinned rubric criterion; no aggregate score is stored.';
comment on column english_essay_self_reviews.disclaimer_acknowledged is
    'The learner explicitly acknowledged that the instructional rubric is not an official ASEAN Scholarship score or prediction.';

commit;
