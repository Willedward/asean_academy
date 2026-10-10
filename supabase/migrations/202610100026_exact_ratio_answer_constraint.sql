begin;

-- Add and validate the expanded response/mode rule before removing the
-- original constraint so existing answer specifications remain protected.
alter table math_answer_specs
    add constraint math_answer_specs_response_mode_check
    check (
        (response_type = 'numeric' and comparison_mode in (
            'exact_numeric', 'absolute_tolerance', 'rounded_dp', 'rounded_sf'
        ))
        or
        (response_type = 'algebraic_expression' and comparison_mode in (
            'symbolic_equivalence', 'prime_factorisation',
            'ordered_numeric_list', 'exact_relation', 'exact_ratio'
        ))
    ) not valid;

alter table math_answer_specs
    validate constraint math_answer_specs_response_mode_check;

alter table math_answer_specs
    drop constraint math_answer_specs_check;

commit;
