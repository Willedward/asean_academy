begin;

-- English targets the Secondary 3-entry test. Existing sessions keep the profile they used.
alter table english_practice_sessions
    alter column exam_profile_key set default 'asean-english-sec3-id-reported-v1';

commit;
