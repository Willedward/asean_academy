begin;

-- A question pool holds at most 40 questions, so a unit with a larger adaptive reserve
-- authors several reserve pools. g3-sec2-g5 has two, which the old one-pool-per-type
-- constraint rejected. Only the checkpoint pool remains limited to one per unit.
alter table unit_checkpoint_pools
    drop constraint unit_checkpoint_pools_unit_version_id_pool_type_key;

create unique index unit_checkpoint_pools_one_checkpoint_per_unit
    on unit_checkpoint_pools (unit_version_id)
    where pool_type = 'unit_checkpoint';

comment on index unit_checkpoint_pools_one_checkpoint_per_unit is
    'Each unit version has one checkpoint pool. It may have several adaptive_reserve pools.';

commit;
