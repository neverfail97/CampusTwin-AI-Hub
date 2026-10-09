-- CampusTwin room occupancy and lock workflow migration
-- Run this in Supabase Dashboard > SQL Editor for an existing CampusTwin database.
-- Safe to re-run. The base schema already defines these columns on fresh installs.

alter table public.rooms
  add column if not exists occupied_by uuid references public.profiles(id) on delete set null;

alter table public.rooms
  add column if not exists occupied_by_name text;

-- Supports quick lookups for rooms currently locked by a faculty member.
create index if not exists rooms_occupied_by_idx
  on public.rooms (occupied_by)
  where occupied_by is not null;

-- Keep existing room status values compatible with the app. The app represents
-- a locked/occupied room with status='Unavailable' and occupied_by set.
