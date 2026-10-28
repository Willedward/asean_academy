begin;

alter type english_question_type add value if not exists 'exam_strategy';

alter type english_error_category add value if not exists 'paper_format';
alter type english_error_category add value if not exists 'instruction_control';
alter type english_error_category add value if not exists 'timing_control';
alter type english_error_category add value if not exists 'independent_conditions';

comment on type english_question_type is
    'Objective English interaction type, including paper orientation, baseline readiness and timed-simulation strategy.';

comment on type english_error_category is
    'Learner-selected cause of an English objective-practice error, including exam-format and independent-attempt strategy.';

commit;
