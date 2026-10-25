begin;

alter type english_question_type add value if not exists 'composition_planning';

alter type english_error_category add value if not exists 'task_topic';
alter type english_error_category add value if not exists 'command_word';
alter type english_error_category add value if not exists 'audience_scope';
alter type english_error_category add value if not exists 'evidence_plan';

comment on type english_question_type is
    'Objective English interaction type, including deterministic composition-task analysis before extended writing.';

comment on type english_error_category is
    'Learner-selected cause of an English objective-practice error, spanning vocabulary, reading, grammar, open cloze and composition planning.';

commit;
