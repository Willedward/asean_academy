begin;

alter table tutor_usage_reservations
    drop constraint tutor_usage_reservations_reserved_cost_micros_sgd_check,
    add constraint tutor_usage_reservations_reserved_cost_micros_sgd_check
        check (reserved_cost_micros_sgd >= 0);

alter table tutor_route_decisions
    drop constraint tutor_route_decisions_reserved_cost_micros_sgd_check,
    add constraint tutor_route_decisions_reserved_cost_micros_sgd_check
        check (reserved_cost_micros_sgd >= 0);

comment on column tutor_usage_reservations.reserved_cost_micros_sgd is
    'Maximum provider cost reserved for the turn; zero is valid for synthetic or free providers.';
comment on column tutor_route_decisions.reserved_cost_micros_sgd is
    'Maximum routed provider cost reserved for the turn; zero is valid for synthetic or free providers.';

commit;
