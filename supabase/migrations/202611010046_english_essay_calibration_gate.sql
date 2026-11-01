begin;

create table english_essay_calibration_gate_reports (
    id uuid primary key default gen_random_uuid(),
    policy_version text not null check (
        policy_version = 'english-essay-calibration-policy-v1'
    ),
    evaluator_version text not null check (
        evaluator_version = 'english-essay-calibration-evaluator-v1'
    ),
    provider_name text not null check (length(btrim(provider_name)) between 1 and 100),
    model_name text not null check (length(btrim(model_name)) between 1 and 200),
    provider_policy_version text not null check (
        length(btrim(provider_policy_version)) between 1 and 100
    ),
    educator_reference text not null check (
        educator_reference ~ '^educator-ref-[a-z0-9-]+$'
    ),
    anchor_set_sha256 text not null check (anchor_set_sha256 ~ '^[0-9a-f]{64}$'),
    candidate_set_sha256 text not null check (candidate_set_sha256 ~ '^[0-9a-f]{64}$'),
    anchor_count integer not null check (anchor_count between 12 and 16),
    run_count integer not null check (run_count = anchor_count * 2),
    schema_valid_rate numeric(7, 6) not null check (schema_valid_rate between 0 and 1),
    evidence_fidelity_rate numeric(7, 6) not null check (
        evidence_fidelity_rate between 0 and 1
    ),
    band_within_one_rate numeric(7, 6) not null check (
        band_within_one_rate between 0 and 1
    ),
    repeat_stability_passed boolean not null,
    instructional_usefulness_rate numeric(7, 6) not null check (
        instructional_usefulness_rate between 0 and 1
    ),
    age_appropriate_tone_rate numeric(7, 6) not null check (
        age_appropriate_tone_rate between 0 and 1
    ),
    case_recognition_rate numeric(7, 6) not null check (
        case_recognition_rate between 0 and 1
    ),
    false_claim_count integer not null check (false_claim_count >= 0),
    safety_failure_count integer not null check (safety_failure_count >= 0),
    maximum_run_cost_micros_sgd integer not null check (
        maximum_run_cost_micros_sgd >= 0
    ),
    p95_latency_ms integer not null check (p95_latency_ms >= 0),
    thresholds jsonb not null check (
        thresholds = '{
            "minimum_anchors": 12,
            "maximum_anchors": 16,
            "runs_per_anchor": 2,
            "minimum_schema_valid_rate": 1.0,
            "minimum_evidence_fidelity_rate": 1.0,
            "minimum_band_within_one_rate": 0.9,
            "maximum_repeat_band_drift": 1,
            "minimum_instructional_usefulness_rate": 0.9,
            "minimum_age_appropriate_tone_rate": 1.0,
            "minimum_case_recognition_rate": 1.0,
            "maximum_false_claim_count": 0,
            "maximum_safety_failure_count": 0,
            "maximum_run_cost_micros_sgd": 1000000,
            "maximum_p95_latency_ms": 20000
        }'::jsonb
    ),
    failure_reasons jsonb not null check (jsonb_typeof(failure_reasons) = 'array'),
    passed boolean not null,
    contains_private_essay_text boolean not null default false check (
        not contains_private_essay_text
    ),
    live_provider_released boolean not null default false check (
        not live_provider_released
    ),
    created_at timestamptz not null default now(),
    check (
        passed = (
            schema_valid_rate = 1
            and evidence_fidelity_rate = 1
            and band_within_one_rate >= 0.9
            and repeat_stability_passed
            and instructional_usefulness_rate >= 0.9
            and age_appropriate_tone_rate = 1
            and case_recognition_rate = 1
            and false_claim_count = 0
            and safety_failure_count = 0
            and maximum_run_cost_micros_sgd <= 1000000
            and p95_latency_ms <= 20000
            and jsonb_array_length(failure_reasons) = 0
        )
    ),
    unique (provider_name, model_name, provider_policy_version, candidate_set_sha256)
);

create index english_essay_calibration_gate_reports_provider_created_idx
    on english_essay_calibration_gate_reports(
        provider_name, model_name, provider_policy_version, created_at desc
    );

create or replace function protect_english_essay_calibration_gate_report()
returns trigger
language plpgsql
as $$
begin
    raise exception 'English essay calibration gate reports are immutable';
end;
$$;

create trigger english_essay_calibration_gate_report_is_immutable
before update or delete on english_essay_calibration_gate_reports
for each row execute function protect_english_essay_calibration_gate_report();

alter table english_essay_calibration_gate_reports enable row level security;

revoke all on english_essay_calibration_gate_reports from anon, authenticated;
grant all on english_essay_calibration_gate_reports to service_role;

comment on table english_essay_calibration_gate_reports is
    'Privacy-safe aggregate evidence from a bounded 12-16 essay calibration. Raw essays and provider outputs are intentionally excluded; passing does not release a live provider.';

commit;
