begin;

-- Existing N1 records remain unchanged. Adding zero counts makes the expanded
-- distribution explicit before new Level 4 and Level 5 questions are imported.
update math_question_banks
set difficulty_counts = difficulty_counts || '{"4": 0}'::jsonb
where not (difficulty_counts ? '4');

update math_question_banks
set difficulty_counts = difficulty_counts || '{"5": 0}'::jsonb
where not (difficulty_counts ? '5');

alter table math_question_banks
    add constraint math_question_banks_difficulty_counts_five_level_check
    check (difficulty_counts ?& array['1', '2', '3', '4', '5']);

-- Add and validate the broader rule before removing the original constraint so
-- there is no interval in which invalid difficulty values can be written.
alter table math_questions
    add constraint math_questions_difficulty_five_level_check
    check (difficulty between 1 and 5) not valid;

alter table math_questions
    validate constraint math_questions_difficulty_five_level_check;

alter table math_questions
    drop constraint math_questions_difficulty_check;

commit;
