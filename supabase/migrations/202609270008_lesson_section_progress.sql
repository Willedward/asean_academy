begin;

create table learner_lesson_section_progress (
    student_id uuid not null references auth.users(id) on delete cascade,
    lesson_section_id uuid not null references lesson_sections(id) on delete cascade,
    completed_at timestamptz not null default now(),
    primary key (student_id, lesson_section_id)
);

create index learner_lesson_section_progress_student_completed_idx
    on learner_lesson_section_progress(student_id, completed_at desc);

alter table learner_lesson_section_progress enable row level security;

create policy learner_lesson_section_progress_owner_read
on learner_lesson_section_progress for select
using (student_id = auth.uid());

grant select on learner_lesson_section_progress to authenticated;

comment on table learner_lesson_section_progress is
    'Explicit learner completion of a section in one immutable lesson revision; this is engagement evidence, not mastery.';

commit;
