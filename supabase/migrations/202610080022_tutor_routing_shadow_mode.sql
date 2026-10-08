begin;

alter table tutor_route_decisions
    add column routing_mode text not null default 'legacy',
    add column recommended_tier text,
    add column recommended_provider_name text,
    add column recommended_model_name text,
    add column recommended_max_output_tokens integer,
    add column recommended_input_cost_per_million_micros_sgd bigint not null default 0,
    add column recommended_output_cost_per_million_micros_sgd bigint not null default 0;

-- The table is append-only at runtime. Temporarily suspend its user trigger so existing
-- rows can receive an explicit historical recommendation during this additive migration.
alter table tutor_route_decisions disable trigger tutor_route_decisions_no_update_or_delete;

update tutor_route_decisions
set recommended_tier = selected_tier,
    recommended_provider_name = provider_name,
    recommended_model_name = model_name,
    recommended_max_output_tokens = max_output_tokens;

alter table tutor_route_decisions enable trigger tutor_route_decisions_no_update_or_delete;

alter table tutor_route_decisions
    alter column routing_mode drop default,
    alter column recommended_tier set not null,
    alter column recommended_provider_name set not null,
    alter column recommended_model_name set not null,
    alter column recommended_max_output_tokens set not null,
    alter column recommended_input_cost_per_million_micros_sgd drop default,
    alter column recommended_output_cost_per_million_micros_sgd drop default,
    add check (routing_mode in ('legacy', 'off', 'shadow', 'live')),
    add check (recommended_tier in ('economy', 'premium')),
    add check (length(btrim(recommended_provider_name)) between 1 and 100),
    add check (length(btrim(recommended_model_name)) between 1 and 100),
    add check (recommended_max_output_tokens > 0),
    add check (recommended_input_cost_per_million_micros_sgd >= 0),
    add check (recommended_output_cost_per_million_micros_sgd >= 0),
    add check (routing_mode <> 'shadow' or selected_tier = 'economy'),
    add check (routing_mode <> 'live' or selected_tier = recommended_tier);

create index tutor_route_decisions_mode_created_idx
    on tutor_route_decisions(routing_mode, created_at desc);
create index tutor_route_decisions_recommended_tier_created_idx
    on tutor_route_decisions(recommended_tier, created_at desc);

comment on column tutor_route_decisions.routing_mode is
    'legacy, off, shadow, or live; shadow always executes the economy route.';
comment on column tutor_route_decisions.selected_tier is
    'The route actually executed and charged against the learner allowance.';
comment on column tutor_route_decisions.recommended_tier is
    'The route recommended by the versioned deterministic policy.';
comment on column tutor_route_decisions.recommended_input_cost_per_million_micros_sgd is
    'Price snapshot used to project the recommendation against actual input usage.';
comment on column tutor_route_decisions.recommended_output_cost_per_million_micros_sgd is
    'Price snapshot used to project the recommendation against actual output usage.';

commit;
