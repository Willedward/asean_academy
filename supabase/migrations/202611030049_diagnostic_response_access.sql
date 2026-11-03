begin;

-- The learning API is the only reader of per-answer diagnostic rows.
revoke all on diagnostic_responses from anon, authenticated;

commit;
