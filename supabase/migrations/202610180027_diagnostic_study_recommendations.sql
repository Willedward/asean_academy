begin;

alter table diagnostic_results
    add column topic_scores jsonb not null default '[]'::jsonb,
    add column study_recommendations jsonb not null default '[]'::jsonb,
    add column recommendation_policy_version text not null default 'topic-readiness-v1',
    add constraint diagnostic_results_topic_scores_array
        check (jsonb_typeof(topic_scores) = 'array'),
    add constraint diagnostic_results_study_recommendations_array
        check (jsonb_typeof(study_recommendations) = 'array'),
    add constraint diagnostic_results_recommendation_policy_present
        check (length(btrim(recommendation_policy_version)) > 0);

comment on column diagnostic_results.topic_scores is
    'Immutable scores aggregated by school level and syllabus topic, avoiding repeated outcome-code collisions.';
comment on column diagnostic_results.study_recommendations is
    'Immutable deterministic lesson recommendations captured when the diagnostic is submitted.';
comment on column diagnostic_results.recommendation_policy_version is
    'Version of the deterministic topic-ranking and lesson-selection policy.';

commit;
