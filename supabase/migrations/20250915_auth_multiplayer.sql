-- Auth + multiplayer + economy schema expansion
create extension if not exists "pgcrypto";

-- Canonical profile bound to Supabase auth.users
create table if not exists profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  handle text unique,
  display_name text,
  region text,
  culture text,
  avatar_url text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists profiles_region_idx on profiles(region);

-- External identity mapping for Discord, GPT, mobile stores, Steam
create table if not exists linked_identities (
  id bigserial primary key,
  user_id uuid not null references profiles(user_id) on delete cascade,
  provider text not null check (provider in ('discord','gpt','mobile_ios','mobile_android','steam','browser')),
  provider_user_id text not null,
  metadata jsonb default '{}'::jsonb,
  linked_at timestamptz default now(),
  unlinked_at timestamptz,
  unique(provider, provider_user_id)
);
create index if not exists linked_identities_user_idx on linked_identities(user_id);

-- Linking tokens for short-lived pairings across platforms
create table if not exists linking_tokens (
  token text primary key,
  user_id uuid references profiles(user_id) on delete cascade,
  provider text not null,
  expires_at timestamptz not null,
  consumed_at timestamptz
);

-- Encrypted astrology payloads with derived fields for queries
create table if not exists astrology_charts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(user_id) on delete cascade,
  encrypted_payload bytea not null,
  derived_profile jsonb default '{}'::jsonb,
  checksum text,
  version int default 1,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists astrology_charts_user_idx on astrology_charts(user_id);

-- Multiplayer containers
create table if not exists parties (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references profiles(user_id) on delete cascade,
  name text,
  visibility text default 'private' check (visibility in ('private','friends','public')),
  created_at timestamptz default now()
);

create table if not exists party_members (
  id bigserial primary key,
  party_id uuid not null references parties(id) on delete cascade,
  user_id uuid not null references profiles(user_id) on delete cascade,
  role text default 'member' check (role in ('owner','officer','member')),
  joined_at timestamptz default now(),
  unique(party_id, user_id)
);
create index if not exists party_members_user_idx on party_members(user_id);

create table if not exists match_sessions (
  id uuid primary key default gen_random_uuid(),
  party_id uuid references parties(id) on delete set null,
  user_id uuid references profiles(user_id) on delete cascade,
  platform text not null,
  status text not null default 'pending' check (status in ('pending','active','finished','quarantined')),
  integrity_state text default 'clean' check (integrity_state in ('clean','suspect','cheat')),
  seed text,
  started_at timestamptz default now(),
  ended_at timestamptz,
  metadata jsonb default '{}'::jsonb
);
create index if not exists match_sessions_user_idx on match_sessions(user_id);

-- Economy primitives
create table if not exists wallets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(user_id) on delete cascade,
  balance bigint default 0,
  currency text default 'STAR',
  updated_at timestamptz default now(),
  unique(user_id, currency)
);

create table if not exists currency_transactions (
  id bigserial primary key,
  wallet_id uuid not null references wallets(id) on delete cascade,
  amount bigint not null,
  reason text not null,
  match_id uuid references match_sessions(id) on delete set null,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);
create index if not exists currency_transactions_wallet_idx on currency_transactions(wallet_id);

create table if not exists inventory_items (
  id bigserial primary key,
  user_id uuid not null references profiles(user_id) on delete cascade,
  item_key text not null,
  quantity int not null default 1,
  metadata jsonb default '{}'::jsonb,
  unique(user_id, item_key)
);
create index if not exists inventory_items_user_idx on inventory_items(user_id);

-- Row Level Security
alter table profiles enable row level security;
alter table linked_identities enable row level security;
alter table linking_tokens enable row level security;
alter table astrology_charts enable row level security;
alter table parties enable row level security;
alter table party_members enable row level security;
alter table match_sessions enable row level security;
alter table wallets enable row level security;
alter table currency_transactions enable row level security;
alter table inventory_items enable row level security;

-- Helper for admin scope detection
create or replace function is_admin(jwt_scope text) returns boolean language sql immutable as $$
  select position('admin' in coalesce(jwt_scope,'')) > 0;
$$;

-- Policies
create policy profiles_self_read on profiles for select using (auth.uid() = user_id or is_admin(current_setting('request.jwt.claims', true)::jsonb->>'scope'));
create policy profiles_self_write on profiles for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy identities_owner on linked_identities for all using (auth.uid() = user_id or is_admin(current_setting('request.jwt.claims', true)::jsonb->>'scope'));

create policy linking_tokens_owner on linking_tokens for select using (auth.uid() = user_id);
create policy linking_tokens_insert on linking_tokens for insert with check (auth.uid() = user_id);

create policy astrology_owner_read on astrology_charts for select using (
  auth.uid() = user_id
  or exists (
    select 1
    from party_members pm_owner
    join party_members pm_viewer on pm_viewer.party_id = pm_owner.party_id
    where pm_owner.user_id = astrology_charts.user_id
      and pm_viewer.user_id = auth.uid()
  )
  or is_admin(current_setting('request.jwt.claims', true)::jsonb->>'scope')
);
create policy astrology_owner_write on astrology_charts for insert, update using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy parties_members_read on parties for select using (
  owner_id = auth.uid()
  or exists (select 1 from party_members pm where pm.party_id = parties.id and pm.user_id = auth.uid())
  or is_admin(current_setting('request.jwt.claims', true)::jsonb->>'scope')
);
create policy parties_owner_write on parties for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());

create policy party_members_read on party_members for select using (
  user_id = auth.uid()
  or exists (select 1 from parties p where p.id = party_members.party_id and p.owner_id = auth.uid())
);
create policy party_members_manage on party_members for all using (
  exists (select 1 from parties p where p.id = party_members.party_id and p.owner_id = auth.uid())
);

create policy matches_owner_read on match_sessions for select using (
  user_id = auth.uid()
  or exists (select 1 from party_members pm where pm.party_id = match_sessions.party_id and pm.user_id = auth.uid())
  or is_admin(current_setting('request.jwt.claims', true)::jsonb->>'scope')
);
create policy matches_owner_write on match_sessions for insert, update using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy wallets_owner_read on wallets for select using (user_id = auth.uid() or is_admin(current_setting('request.jwt.claims', true)::jsonb->>'scope'));
create policy wallets_owner_write on wallets for insert, update using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy transactions_owner_read on currency_transactions for select using (
  exists (select 1 from wallets w where w.id = currency_transactions.wallet_id and w.user_id = auth.uid())
);
create policy transactions_owner_insert on currency_transactions for insert with check (
  exists (select 1 from wallets w where w.id = currency_transactions.wallet_id and w.user_id = auth.uid())
);

create policy inventory_owner on inventory_items for all using (user_id = auth.uid()) with check (user_id = auth.uid());
