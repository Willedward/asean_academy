begin;

alter type beta_audit_event_type add value if not exists 'tutor_evaluation_conversation_created';
alter type beta_audit_event_type add value if not exists 'tutor_evaluation_conversation_turn_created';

create table tutor_evaluation_conversations (
    id uuid primary key default gen_random_uuid(),
    suite_id text not null,
    suite_version text not null,
    case_id text not null,
    case_snapshot jsonb not null,
    provider text not null check (provider in ('synthetic', 'gemini')),
    model_name text not null,
    prompt_version text not null,
    created_by uuid not null references profiles(id) on delete restrict,
    request_id text not null,
    created_at timestamptz not null default now()
);

create index tutor_evaluation_conversations_owner_case_created_idx
    on tutor_evaluation_conversations (created_by, case_id, created_at desc);

create table tutor_evaluation_conversation_turns (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references tutor_evaluation_conversations(id) on delete restrict,
    turn_index integer not null check (turn_index > 0),
    learner_message text not null check (length(btrim(learner_message)) between 1 and 1200),
    mode text not null check (mode in (
        'clarify_question',
        'diagnose_misconception',
        'socratic_prompt',
        'alternative_explanation',
        'analogous_example',
        'solution_explanation',
        'lesson_recommendation'
    )),
    automated_pass boolean not null,
    latency_ms integer not null check (latency_ms >= 0),
    input_tokens integer not null check (input_tokens >= 0),
    output_tokens integer not null check (output_tokens >= 0),
    cost_micros_sgd bigint not null check (cost_micros_sgd >= 0),
    response_blocks jsonb not null,
    suggested_replies jsonb not null,
    recommended_next_action text,
    automated_checks jsonb not null,
    provider_error text,
    created_by uuid not null references profiles(id) on delete restrict,
    request_id text not null,
    created_at timestamptz not null default now(),
    unique (conversation_id, turn_index)
);

create index tutor_evaluation_conversation_turns_conversation_idx
    on tutor_evaluation_conversation_turns (conversation_id, turn_index);

create trigger tutor_evaluation_conversations_append_only
before update or delete on tutor_evaluation_conversations
for each row execute function reject_tutor_evaluation_mutation();

create trigger tutor_evaluation_conversation_turns_append_only
before update or delete on tutor_evaluation_conversation_turns
for each row execute function reject_tutor_evaluation_mutation();

alter table tutor_evaluation_conversations enable row level security;
alter table tutor_evaluation_conversation_turns enable row level security;
revoke all on tutor_evaluation_conversations from anon, authenticated;
revoke all on tutor_evaluation_conversation_turns from anon, authenticated;
grant all on tutor_evaluation_conversations to service_role;
grant all on tutor_evaluation_conversation_turns to service_role;

commit;
