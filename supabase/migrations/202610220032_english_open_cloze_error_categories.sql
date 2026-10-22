begin;

alter type english_error_category add value if not exists 'gap_role';
alter type english_error_category add value if not exists 'local_grammar';
alter type english_error_category add value if not exists 'cohesion_clue';
alter type english_error_category add value if not exists 'entry_accuracy';

comment on type english_error_category is
    'Learner-selected cause of an English objective-practice error, spanning vocabulary, reading, grammar and open cloze.';

commit;
