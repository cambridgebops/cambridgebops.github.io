-- Applied to project xixflbudqcpzjxdijlta on 2026-10-30 (as migration events_and_scrape_runs).
create extension if not exists pgcrypto;

create table public.events (
  id uuid primary key default gen_random_uuid(),
  title text not null check (char_length(title) between 2 and 120),
  starts_at timestamptz not null,
  ends_at timestamptz,
  venue text not null check (char_length(venue) between 1 and 120),
  kind text not null default 'other' check (kind in ('bop','gig','quiz','formal','comedy','party','other')),
  host text check (host is null or char_length(host) <= 120),
  price text check (price is null or char_length(price) <= 40),
  url text check (url is null or (url ~* '^https?://' and char_length(url) <= 500)),
  details text check (details is null or char_length(details) <= 500),
  source text not null default 'submission',      -- 'submission' or the scraped source's name
  source_key text unique,                         -- dedup key for scraped events: <source>:<yyyy-mm-dd>:<title-slug>
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  created_at timestamptz not null default now()
);
create index events_upcoming_idx on public.events (starts_at) where status = 'approved';

create table public.scrape_runs (
  id bigint generated always as identity primary key,
  ran_at timestamptz not null default now(),
  sources jsonb not null default '[]'::jsonb,     -- [{name, url, ok, found}]
  added integer not null default 0,
  reviewed integer not null default 0,
  notes text
);

alter table public.events enable row level security;
alter table public.scrape_runs enable row level security;

-- The page reads approved, upcoming events with the publishable key.
create policy "public reads upcoming approved events" on public.events
  for select to anon, authenticated
  using (status = 'approved' and starts_at > now() - interval '1 day');

-- The form inserts pending submissions; status and source cannot be set by the client.
create policy "public submits pending events" on public.events
  for insert to anon, authenticated
  with check (status = 'pending' and source = 'submission' and source_key is null);

create policy "public reads scrape runs" on public.scrape_runs
  for select to anon, authenticated using (true);

revoke update, delete on public.events from anon, authenticated;
revoke insert, update, delete on public.scrape_runs from anon, authenticated;
