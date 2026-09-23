#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL to a disposable PostgreSQL database.}"

psql -X "${DATABASE_URL}" -v ON_ERROR_STOP=1 <<'SQL'
create schema if not exists auth;
create table if not exists auth.users (
    id uuid primary key,
    email text,
    created_at timestamptz not null default now()
);
create or replace function auth.uid()
returns uuid
language sql
stable
as $$ select null::uuid $$;
SQL

for migration in supabase/migrations/*.sql; do
    echo "Applying ${migration}"
    psql -X "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "${migration}"
done

echo "All migrations applied successfully."
