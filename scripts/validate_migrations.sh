#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL to a disposable PostgreSQL database.}"

psql -X "${DATABASE_URL}" -v ON_ERROR_STOP=1 <<'SQL'
do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'anon') then
        create role anon nologin;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'authenticated') then
        create role authenticated nologin;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'service_role') then
        create role service_role nologin bypassrls;
    end if;
end
$$;

create schema if not exists auth;
grant usage on schema auth to authenticated;
create table if not exists auth.users (
    id uuid primary key,
    email text,
    created_at timestamptz not null default now()
);
create or replace function auth.uid()
returns uuid
language sql
stable
as $$
    select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;
SQL

for migration in supabase/migrations/*.sql; do
    echo "Applying ${migration}"
    psql -X "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "${migration}"
done

echo "All migrations applied successfully."
