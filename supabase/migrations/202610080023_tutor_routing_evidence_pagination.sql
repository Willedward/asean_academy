begin;

create index tutor_route_decisions_created_id_idx
    on tutor_route_decisions(created_at desc, id desc);

comment on index tutor_route_decisions_created_id_idx is
    'Stable cursor pagination for restricted administrator routing evidence.';

commit;
