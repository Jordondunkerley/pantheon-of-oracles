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
  client_action_id text,
  metadata jsonb,
  created_at timestamptz default now()
);

create unique index if not exists oracle_actions_client_action_key
  on oracle_actions(oracle_id, client_action_id)
  where client_action_id is not null;

-- Player accounts store the full profile payload provided by the Pantheon GPT
-- router. The player_id is a stable, client-visible identifier, while profile
-- captures the rich nested JSON from the templates (factions, stats, tokens,
-- etc.).
create table if not exists player_accounts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  player_id text not null unique,
  username text,
  email text,
  profile jsonb not null default '{}'::jsonb,
  created_at timestamptz default now()
);
create unique index if not exists player_accounts_user_id_key on player_accounts(user_id);

-- Oracle profiles persist the detailed oracle template payloads. oracle_id is
-- the externally visible identifier supplied by clients; profile preserves all
-- nested metadata for battles, rituals, factions, and visual attributes.
create table if not exists oracle_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  oracle_id text not null unique,
  oracle_name text,
  archetype text,
  profile jsonb not null default '{}'::jsonb,
  created_at timestamptz default now()
);
create index if not exists oracle_profiles_user_id_idx on oracle_profiles(user_id);

alter table users enable row level security;
alter table oracles enable row level security;
alter table oracle_actions enable row level security;
alter table player_accounts enable row level security;
alter table oracle_profiles enable row level security;

-- permissive starter policies (tighten later)
create policy users_read on users for select using (true);
create policy users_write on users for insert with check (true);

create policy oracles_read on oracles for select using (true);
create policy oracles_upsert on oracles for insert with check (true);

create policy actions_read on oracle_actions for select using (true);
create policy actions_write on oracle_actions for insert with check (true);

create policy player_accounts_read on player_accounts for select using (true);
create policy player_accounts_upsert on player_accounts for insert with check (true);
create policy player_accounts_update on player_accounts for update using (true) with check (true);

create policy oracle_profiles_read on oracle_profiles for select using (true);
create policy oracle_profiles_upsert on oracle_profiles for insert with check (true);
create policy oracle_profiles_update on oracle_profiles for update using (true) with check (true);
