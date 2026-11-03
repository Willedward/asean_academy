begin;

create or replace function reject_english_learning_evidence_mutation()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'English learning evidence is immutable';
end;
$$;

create or replace function protect_english_essay_submission()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'English essay submissions are immutable';
end;
$$;

create or replace function protect_english_essay_self_review()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'English essay self-reviews are immutable';
end;
$$;

create or replace function protect_english_essay_marking_feedback()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'English essay marking feedback is immutable';
end;
$$;

create or replace function protect_english_essay_provider_feedback()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'Essay provider feedback is immutable';
end;
$$;

create or replace function protect_english_essay_feedback_usefulness()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'Essay feedback usefulness responses are immutable';
end;
$$;

-- This function also guards release tables that have no student_id, so only read that
-- column for consent events.
create or replace function protect_english_essay_release_evidence()
returns trigger
language plpgsql
as $$
begin
    if tg_table_name = 'english_essay_processing_consent_events' and tg_op = 'DELETE' then
        if current_setting('app.account_deletion_target', true) = old.student_id::text then
            return old;
        end if;
    end if;
    raise exception 'English essay release evidence is immutable';
end;
$$;

commit;
