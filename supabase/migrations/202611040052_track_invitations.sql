begin;

-- One invitation code can enrol a learner in every course of a track. The existing
-- course_version_id stays the first course, so single-course invitations are unchanged.
alter table beta_invitations
    add column target_track text
        check (target_track is null or length(btrim(target_track)) between 1 and 80);

create table beta_invitation_additional_courses (
    invitation_id uuid not null references beta_invitations(id) on delete cascade,
    course_version_id uuid not null references course_versions(id) on delete restrict,
    primary key (invitation_id, course_version_id)
);

create index beta_invitation_additional_courses_version_idx
    on beta_invitation_additional_courses(course_version_id);

alter table beta_invitation_additional_courses enable row level security;
revoke all on beta_invitation_additional_courses from anon, authenticated;

comment on column beta_invitations.target_track is
    'Track recorded on the learner profile when this invitation covers a whole track.';
comment on table beta_invitation_additional_courses is
    'Further courses enrolled by a track invitation, beyond beta_invitations.course_version_id.';

commit;
