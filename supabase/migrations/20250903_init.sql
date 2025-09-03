-- Initial schema aligning with GPT Oracron + Router

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  created_at timestamptz default now()
);

create table if not exists oracles (
  id uuid primary key default gen_random_uuid(),
  code text not null,                -- e.g., ORYONOS, SEQUOIA
  name text not null,
  role text,
  rules jsonb default '{}'::jsonb,   -- compact rules from GPT patches
  created_at timestamptz default now()
);
create unique index if not exists oracles_code_key on oracles(code);

create table if not exists oracle_actions (
  id bigserial primary key,
  oracle_id uuid not null references oracles(id) on delete cascade,
  player_id text not null,
  action text not null,
  metadata jsonb,
  created_at timestamptz default now()
);

alter table users enable row level security;
alter table oracles enable row level security;
alter table oracle_actions enable row level security;

-- permissive starter policies (tighten later)
create policy users_read on users for select using (true);
create policy users_write on users for insert with check (true);

create policy oracles_read on oracles for select using (true);
create policy oracles_upsert on oracles for insert with check (true);

create policy actions_read on oracle_actions for select using (true);
create policy actions_write on oracle_actions for insert with check (true);
