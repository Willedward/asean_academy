begin;

alter table content_review_records
    drop constraint if exists content_review_records_item_kind_check;
alter table content_review_records
    add constraint content_review_records_item_kind_check
    check (item_kind in (
        'course', 'lesson', 'question', 'tutor_grounding',
        'english_lesson', 'english_checkpoint_form',
        'english_passage', 'english_question'
    ));

alter table content_lifecycle_requests
    drop constraint if exists content_lifecycle_requests_item_kind_check;
alter table content_lifecycle_requests
    add constraint content_lifecycle_requests_item_kind_check
    check (item_kind in (
        'course', 'lesson', 'question', 'tutor_grounding',
        'english_lesson', 'english_checkpoint_form',
        'english_passage', 'english_question'
    ));

comment on constraint content_review_records_item_kind_check on content_review_records is
    'Reviewable Git-authored Mathematics, English, checkpoint-form and tutor-grounding records.';

commit;
