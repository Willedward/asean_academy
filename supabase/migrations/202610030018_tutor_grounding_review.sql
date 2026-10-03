begin;

alter table content_review_records
    drop constraint if exists content_review_records_item_kind_check;

alter table content_review_records
    add constraint content_review_records_item_kind_check
    check (item_kind in ('course', 'lesson', 'question', 'tutor_grounding'));

comment on constraint content_review_records_item_kind_check on content_review_records is
    'Human review applies to learner content and protected AI tutor grounding revisions.';

commit;
