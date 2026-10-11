begin;

-- N2 ratio questions use the deterministic exact-ratio checker already
-- supported by the authored JSON contract and application domain.
alter type math_comparison_mode add value if not exists 'exact_ratio';

commit;
