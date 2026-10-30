begin;

create table english_essay_drafts (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    prompt_version_id uuid not null
        references english_essay_prompt_versions(id) on delete restrict,
    body text not null default '' check (length(body) <= 20000),
    word_count integer not null default 0 check (word_count >= 0),
    edit_revision integer not null default 1 check (edit_revision > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (student_id, prompt_version_id)
);

create table english_essay_draft_idempotency_keys (
    student_id uuid not null references auth.users(id) on delete cascade,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    draft_id uuid not null references english_essay_drafts(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (student_id, idempotency_key)
);

create index english_essay_drafts_student_updated_idx
    on english_essay_drafts(student_id, updated_at desc);

create or replace function protect_english_essay_draft_identity()
returns trigger
language plpgsql
as $$
begin
    if row(old.student_id, old.prompt_version_id, old.created_at) is distinct from
       row(new.student_id, new.prompt_version_id, new.created_at) then
        raise exception 'English essay draft ownership and prompt revision are immutable';
    end if;
    if new.edit_revision <> old.edit_revision + 1 then
        raise exception 'English essay draft edit revision must increase by exactly one';
    end if;
    if new.updated_at <= old.updated_at then
        raise exception 'English essay draft updated_at must advance';
    end if;
    return new;
end;
$$;

create trigger english_essay_draft_identity_is_immutable
before update on english_essay_drafts
for each row execute function protect_english_essay_draft_identity();

alter table english_essay_drafts enable row level security;
alter table english_essay_draft_idempotency_keys enable row level security;

create policy english_essay_drafts_owner_read
on english_essay_drafts for select using (student_id = auth.uid());

create policy english_essay_draft_idempotency_owner_read
on english_essay_draft_idempotency_keys for select using (student_id = auth.uid());

grant select on english_essay_drafts to authenticated;
grant select on english_essay_draft_idempotency_keys to authenticated;

comment on table english_essay_drafts is
    'Mutable learner-owned essay working copies pinned to one immutable prompt revision. They are not submissions.';
comment on column english_essay_drafts.edit_revision is
    'Optimistic concurrency token incremented once per successful autosave.';

commit;
