begin;

alter type beta_audit_event_type add value if not exists 'content_review_recorded';
alter type beta_audit_event_type add value if not exists 'content_publication_requested';
alter type beta_audit_event_type add value if not exists 'content_retirement_requested';

create table content_review_records (
    id uuid primary key default gen_random_uuid(),
    item_kind text not null check (item_kind in ('course', 'lesson', 'question')),
    stable_key text not null check (length(btrim(stable_key)) > 0),
    source_revision integer not null check (source_revision > 0),
    source_content_sha256 text not null check (source_content_sha256 ~ '^[0-9a-f]{64}$'),
    review_fingerprint text not null check (review_fingerprint ~ '^[0-9a-f]{64}$'),
    dimension text not null check (dimension in ('mathematics', 'editorial')),
    decision text not null check (decision in ('approved', 'changes_requested')),
    reviewer_id uuid not null references profiles(id) on delete restrict,
    notes text not null check (length(btrim(notes)) between 10 and 2000),
    request_id text not null check (length(btrim(request_id)) > 0),
    created_at timestamptz not null default now()
);

create index content_review_records_lookup_idx
    on content_review_records(item_kind, stable_key, review_fingerprint, dimension, created_at desc);

create table content_lifecycle_requests (
    id uuid primary key default gen_random_uuid(),
    item_kind text not null check (item_kind in ('course', 'lesson', 'question')),
    stable_key text not null check (length(btrim(stable_key)) > 0),
    source_revision integer not null check (source_revision > 0),
    source_content_sha256 text not null check (source_content_sha256 ~ '^[0-9a-f]{64}$'),
    review_fingerprint text not null check (review_fingerprint ~ '^[0-9a-f]{64}$'),
    action text not null check (action in ('publish', 'retire')),
    requested_by uuid not null references profiles(id) on delete restrict,
    reason text not null check (length(btrim(reason)) between 10 and 2000),
    request_id text not null check (length(btrim(request_id)) > 0),
    created_at timestamptz not null default now()
);

create index content_lifecycle_requests_lookup_idx
    on content_lifecycle_requests(item_kind, stable_key, review_fingerprint, created_at desc);

alter table content_review_records enable row level security;
alter table content_lifecycle_requests enable row level security;
revoke all on content_review_records from anon, authenticated;
revoke all on content_lifecycle_requests from anon, authenticated;
grant all on content_review_records to service_role;
grant all on content_lifecycle_requests to service_role;

create function reject_content_workflow_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'content workflow records are append-only';
end;
$$;

create trigger content_review_records_no_update_or_delete
before update or delete on content_review_records
for each row execute function reject_content_workflow_mutation();

create trigger content_lifecycle_requests_no_update_or_delete
before update or delete on content_lifecycle_requests
for each row execute function reject_content_workflow_mutation();

comment on table content_review_records is
    'Append-only human review decisions bound to a semantic content fingerprint.';
comment on table content_lifecycle_requests is
    'Append-only release requests. Git-authored status and deployment imports remain authoritative.';

commit;
