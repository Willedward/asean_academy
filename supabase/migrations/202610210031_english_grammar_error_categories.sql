begin;

alter type english_error_category add value if not exists 'clause_structure';
alter type english_error_category add value if not exists 'boundary_choice';
alter type english_error_category add value if not exists 'agreement_control';

comment on type english_error_category is
    'Learner-selected cause of an English objective-practice error, spanning vocabulary, reading and grammar.';

commit;
