begin;

alter type beta_audit_event_type add value if not exists
    'english_essay_calibration_report_recorded';
alter type beta_audit_event_type add value if not exists
    'english_essay_privacy_review_recorded';
alter type beta_audit_event_type add value if not exists
    'english_essay_feedback_released';
alter type beta_audit_event_type add value if not exists
    'english_essay_feedback_suspended';
alter type beta_audit_event_type add value if not exists
    'english_essay_consent_recorded';

create table english_essay_feedback_privacy_reviews (
    id uuid primary key default gen_random_uuid(),
    calibration_gate_report_id uuid not null
        references english_essay_calibration_gate_reports(id) on delete restrict,
    reviewer_user_id uuid not null references auth.users(id) on delete restrict,
    guardian_consent_process_verified boolean not null,
    consent_policy_version text not null check (
        consent_policy_version ~ '^english-essay-consent-v[0-9]+$'
    ),
    retention_policy_version text not null check (
        retention_policy_version ~ '^english-essay-retention-v[0-9]+$'
    ),
    retention_days integer not null check (retention_days between 1 and 3650),
    deletion_workflow_verified boolean not null,
    raw_essay_logging_excluded boolean not null,
    provider_agreement_reference text not null check (
        provider_agreement_reference ~ '^provider-agreement-ref-[a-z0-9-]+$'
    ),
    regional_privacy_review_reference text not null check (
        regional_privacy_review_reference ~ '^privacy-review-ref-[a-z0-9-]+$'
    ),
    provider_data_region text not null check (
        length(btrim(provider_data_region)) between 2 and 100
    ),
    provider_retention_days integer not null check (
        provider_retention_days between 0 and retention_days
    ),
    subprocessors_reviewed boolean not null,
    automated_safety_classification_verified boolean not null,
    safeguarding_contact_reference text not null check (
        safeguarding_contact_reference ~ '^safeguarding-ref-[a-z0-9-]+$'
    ),
    review_notes text not null check (length(btrim(review_notes)) between 10 and 2000),
    request_id text not null unique check (length(btrim(request_id)) between 8 and 200),
    passed boolean generated always as (
        guardian_consent_process_verified
        and deletion_workflow_verified
        and raw_essay_logging_excluded
        and subprocessors_reviewed
        and automated_safety_classification_verified
    ) stored,
    created_at timestamptz not null default now()
);

create index english_essay_feedback_privacy_reviews_gate_created_idx
    on english_essay_feedback_privacy_reviews(calibration_gate_report_id, created_at desc);

create table english_essay_feedback_release_events (
    id uuid primary key default gen_random_uuid(),
    calibration_gate_report_id uuid not null
        references english_essay_calibration_gate_reports(id) on delete restrict,
    privacy_review_id uuid not null
        references english_essay_feedback_privacy_reviews(id) on delete restrict,
    actor_user_id uuid not null references auth.users(id) on delete restrict,
    action text not null check (action in ('released', 'suspended')),
    reason text not null check (length(btrim(reason)) between 10 and 1000),
    request_id text not null unique check (length(btrim(request_id)) between 8 and 200),
    created_at timestamptz not null default now()
);

create index english_essay_feedback_release_events_gate_created_idx
    on english_essay_feedback_release_events(calibration_gate_report_id, created_at desc);

create table english_essay_processing_consent_events (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    actor_user_id uuid not null references auth.users(id) on delete restrict,
    action text not null check (action in ('granted', 'revoked')),
    consent_policy_version text not null check (
        consent_policy_version ~ '^english-essay-consent-v[0-9]+$'
    ),
    guardian_reference_sha256 text check (
        guardian_reference_sha256 is null
        or guardian_reference_sha256 ~ '^[0-9a-f]{64}$'
    ),
    expires_at timestamptz,
    reason text not null check (length(btrim(reason)) between 10 and 1000),
    request_id text not null unique check (length(btrim(request_id)) between 8 and 200),
    created_at timestamptz not null default now(),
    check (
        (action = 'granted' and guardian_reference_sha256 is not null
            and expires_at is not null and expires_at > created_at)
        or (action = 'revoked' and guardian_reference_sha256 is null
            and expires_at is null)
    )
);

create index english_essay_processing_consent_events_student_created_idx
    on english_essay_processing_consent_events(student_id, created_at desc);

create or replace function validate_english_essay_privacy_review()
returns trigger
language plpgsql
as $$
begin
    if not exists (
        select 1 from profiles
         where id = new.reviewer_user_id and role = 'academic_admin'
    ) then
        raise exception 'English essay privacy review requires an academic administrator';
    end if;
    if not exists (
        select 1 from english_essay_calibration_gate_reports
         where id = new.calibration_gate_report_id
    ) then
        raise exception 'English essay privacy review requires calibration evidence';
    end if;
    return new;
end;
$$;

create or replace function validate_english_essay_feedback_release_event()
returns trigger
language plpgsql
as $$
declare
    calibration english_essay_calibration_gate_reports%rowtype;
    privacy_review english_essay_feedback_privacy_reviews%rowtype;
begin
    if not exists (
        select 1 from profiles
         where id = new.actor_user_id and role = 'academic_admin'
    ) then
        raise exception 'English essay release decisions require an academic administrator';
    end if;
    select * into calibration from english_essay_calibration_gate_reports
     where id = new.calibration_gate_report_id;
    select * into privacy_review from english_essay_feedback_privacy_reviews
     where id = new.privacy_review_id;
    if calibration.id is null or privacy_review.id is null
       or privacy_review.calibration_gate_report_id <> calibration.id then
        raise exception 'English essay release evidence does not match';
    end if;
    if new.action = 'released' and (not calibration.passed or not privacy_review.passed) then
        raise exception 'English essay feedback cannot be released while a gate is failing';
    end if;
    return new;
end;
$$;

create or replace function validate_english_essay_processing_consent_event()
returns trigger
language plpgsql
as $$
begin
    if not exists (
        select 1 from profiles
         where id = new.actor_user_id and role = 'academic_admin'
    ) then
        raise exception 'English essay consent evidence requires an academic administrator';
    end if;
    if not exists (
        select 1 from profiles
         where id = new.student_id and role = 'student'
    ) then
        raise exception 'English essay consent evidence requires a student account';
    end if;
    return new;
end;
$$;

create or replace function protect_english_essay_release_evidence()
returns trigger
language plpgsql
as $$
begin
    raise exception 'English essay release evidence is immutable';
end;
$$;

create trigger english_essay_feedback_privacy_review_is_valid
before insert on english_essay_feedback_privacy_reviews
for each row execute function validate_english_essay_privacy_review();
create trigger english_essay_feedback_privacy_review_is_immutable
before update or delete on english_essay_feedback_privacy_reviews
for each row execute function protect_english_essay_release_evidence();

create trigger english_essay_feedback_release_event_is_valid
before insert on english_essay_feedback_release_events
for each row execute function validate_english_essay_feedback_release_event();
create trigger english_essay_feedback_release_event_is_immutable
before update or delete on english_essay_feedback_release_events
for each row execute function protect_english_essay_release_evidence();

create trigger english_essay_processing_consent_event_is_valid
before insert on english_essay_processing_consent_events
for each row execute function validate_english_essay_processing_consent_event();
create trigger english_essay_processing_consent_event_is_immutable
before update or delete on english_essay_processing_consent_events
for each row execute function protect_english_essay_release_evidence();

alter table english_essay_feedback_privacy_reviews enable row level security;
alter table english_essay_feedback_release_events enable row level security;
alter table english_essay_processing_consent_events enable row level security;

revoke all on english_essay_feedback_privacy_reviews,
    english_essay_feedback_release_events,
    english_essay_processing_consent_events from anon, authenticated;
grant all on english_essay_feedback_privacy_reviews,
    english_essay_feedback_release_events,
    english_essay_processing_consent_events to service_role;

comment on table english_essay_feedback_privacy_reviews is
    'Immutable academic-administrator evidence for consent, retention, deletion, provider handling, safety and safeguarding controls.';
comment on table english_essay_feedback_release_events is
    'Append-only explicit release or suspension decisions. A release requires passing calibration and privacy evidence.';
comment on table english_essay_processing_consent_events is
    'Append-only guardian-consent evidence using only an opaque SHA-256 guardian reference; no guardian identity is stored.';

commit;
