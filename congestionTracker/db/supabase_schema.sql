-- Supabase schema for City Congestion Tracker

create table if not exists intersections (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  lat double precision not null,
  lon double precision not null,
  priority_level text not null default 'normal',
  created_at timestamptz not null default now()
);

create table if not exists congestion_readings (
  id bigserial primary key,
  intersection_id uuid not null references intersections(id) on delete cascade,
  timestamp_utc timestamptz not null,
  congestion_level integer not null check (congestion_level between 0 and 100),
  speed_kmh double precision,
  delay_sec double precision,
  source text not null default 'synthetic'
);

create index if not exists idx_congestion_intersection_time
  on congestion_readings (intersection_id, timestamp_utc);

create index if not exists idx_congestion_time
  on congestion_readings (timestamp_utc);

