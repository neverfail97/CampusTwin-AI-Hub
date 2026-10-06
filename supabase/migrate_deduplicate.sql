-- CampusConnect repair migration for an existing database.
-- Keeps one copy of every exact timetable booking, then prevents future duplicates.
with ranked as (
  select id, row_number() over (
    partition by day, start_time, end_time, room_id, section, subject_id, faculty_id
    order by created_at asc, id asc
  ) as rn
  from public.timetable
)
delete from public.timetable t
using ranked r
where t.id = r.id and r.rn > 1;

drop index if exists public.timetable_natural_key_idx;
create unique index public.timetable_natural_key_idx
  on public.timetable (day, start_time, end_time, room_id, section, subject_id, faculty_id);

with ranked as (
  select id, row_number() over (
    partition by room_id, lower(name)
    order by created_at asc, id asc
  ) as rn
  from public.resources
)
delete from public.resources r
using ranked x
where r.id = x.id and x.rn > 1;

drop index if exists public.resources_room_name_idx;
create unique index public.resources_room_name_idx
  on public.resources (room_id, lower(name));
