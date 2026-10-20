begin;

alter table content_review_records
    drop constraint if exists content_review_records_item_kind_check;
alter table content_review_records
    add constraint content_review_records_item_kind_check
    check (item_kind in (
        'course', 'lesson', 'question', 'tutor_grounding',
        'english_lesson', 'english_passage', 'english_question'
    ));

alter table content_review_records
    drop constraint if exists content_review_records_dimension_check;
alter table content_review_records
    add constraint content_review_records_dimension_check
    check (dimension in ('mathematics', 'english', 'editorial'));

alter table content_lifecycle_requests
    drop constraint if exists content_lifecycle_requests_item_kind_check;
alter table content_lifecycle_requests
    add constraint content_lifecycle_requests_item_kind_check
    check (item_kind in (
        'course', 'lesson', 'question', 'tutor_grounding',
        'english_lesson', 'english_passage', 'english_question'
    ));

comment on column content_review_records.dimension is
    'Subject review (Mathematics or English) or editorial review, bound to one exact semantic fingerprint.';

commit;
