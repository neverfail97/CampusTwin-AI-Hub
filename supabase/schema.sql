-- Smart Campus Management - fresh Supabase PostgreSQL schema
-- Run this file in Supabase Dashboard > SQL Editor. It deliberately contains no records.

create extension if not exists "pgcrypto";

create table if not exists public.profiles (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(trim(name)) between 2 and 100),
  email text not null unique check (email = lower(email)),
  role text not null check (role in ('student', 'faculty', 'worker')),
  access_code_hash text not null,
  student_id text unique,
  attendance_pct numeric(5,2) not null default 88.5 check (attendance_pct between 0 and 100),
  target_class text not null default 'CSE-A',
  target_subject text not null default '',
  target_time text not null default '',
  floor text not null default 'Ground Floor',
  created_at timestamptz not null default now()
);

create table if not exists public.rooms (
  id uuid primary key default gen_random_uuid(),
  room_number text not null unique,
  room_name text not null,
  category text not null check (category in ('Classroom', 'Laboratory', 'Staff Room', 'HOD Room', 'Faculty Room', 'Seminar Hall', 'Toilet', 'Other')),
  floor text not null,
  capacity integer not null default 0 check (capacity >= 0),
  benches integer not null default 0 check (benches >= 0),
  occupied_seats integer not null default 0 check (occupied_seats >= 0 and occupied_seats <= capacity),
  projector text not null default 'Not applicable',
  board text not null default 'Not applicable',
  internet text not null default 'Not applicable',
  other_resources text not null default '',
  status text not null default 'Empty' check (status in ('Available', 'Attention', 'Unavailable', 'Empty')),
  department text not null default '',
  occupied_by uuid references public.profiles(id) on delete set null,
  occupied_by_name text,
  created_at timestamptz not null default now()
);

create table if not exists public.resources (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references public.rooms(id) on delete cascade,
  name text not null,
  category text not null default 'General',
  total_count integer not null default 1 check (total_count >= 0),
  available_count integer not null default 1 check (available_count >= 0 and available_count <= total_count),
  status text not null default 'Available' check (status in ('Available','Limited','Unavailable')),
  created_at timestamptz not null default now()
);

create table if not exists public.subjects (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  semester integer not null check (semester between 1 and 8),
  credits numeric(3,1) not null check (credits > 0),
  course_category text not null default 'Core',
  syllabus_units integer not null default 5 check (syllabus_units > 0),
  faculty_id uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.issues (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references public.rooms(id) on delete restrict,
  title text not null, category text not null,
  priority text not null check (priority in ('Low','Medium','High','Critical')),
  priority_rank integer not null check (priority_rank between 1 and 4),
  description text not null, status text not null default 'Open' check (status in ('Open','In Progress','Resolved','Verified')),
  reported_by uuid not null references public.profiles(id) on delete restrict,
  assigned_to uuid references public.profiles(id) on delete set null,
  worker_note text not null default '', faculty_verification text not null default 'Pending',
  created_at timestamptz not null default now(), updated_at timestamptz
);

create table if not exists public.timetable (
  id uuid primary key default gen_random_uuid(),
  day text not null check (day in ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday')),
  day_order integer not null check (day_order between 1 and 6),
  start_time time not null, end_time time not null check (end_time > start_time),
  room_id uuid not null references public.rooms(id) on delete restrict,
  section text not null, subject_id uuid not null references public.subjects(id) on delete restrict,
  faculty_id uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.eco_reports (
  id uuid primary key default gen_random_uuid(),
  email text not null check (position('@' in email) > 1),
  location text not null,
  category text not null,
  description text not null,
  photo_name text not null default '',
  reporter_name text not null default '',
  reporter_role text not null default '',
  worker_reply text not null default '',
  resolved_by_name text,
  status text not null default 'Assigned' check (status in ('Assigned','In Progress','Resolved','Verified')),
  created_at timestamptz not null default now()
);

-- Upgrade an older version of this schema without deleting data.
alter table public.profiles add column if not exists student_id text unique;
alter table public.profiles add column if not exists attendance_pct numeric(5,2) not null default 88.5 check (attendance_pct between 0 and 100);
alter table public.profiles add column if not exists target_class text not null default 'CSE-A';
alter table public.profiles add column if not exists target_subject text not null default '';
alter table public.profiles add column if not exists target_time text not null default '';
alter table public.profiles add column if not exists floor text not null default 'Ground Floor';
alter table public.rooms add column if not exists department text not null default '';
alter table public.rooms add column if not exists occupied_by uuid references public.profiles(id) on delete set null;
alter table public.rooms add column if not exists occupied_by_name text;
alter table public.eco_reports add column if not exists reporter_name text not null default '';
alter table public.eco_reports add column if not exists reporter_role text not null default '';
alter table public.eco_reports add column if not exists worker_reply text not null default '';
alter table public.eco_reports add column if not exists resolved_by_name text;

create table if not exists public.syllabus_progress (
  id uuid primary key default gen_random_uuid(),
  subject_id uuid not null references public.subjects(id) on delete cascade,
  week_number integer not null check (week_number between 1 and 30),
  coverage_percent numeric(5,2) not null check (coverage_percent between 0 and 100),
  topics_covered text not null, updated_by uuid references public.profiles(id) on delete set null,
  updated_at timestamptz not null default now(),
  unique(subject_id, week_number)
);

create index if not exists rooms_category_idx on public.rooms(category);
create index if not exists resources_room_idx on public.resources(room_id);
create index if not exists issues_priority_idx on public.issues(priority_rank desc, created_at desc);
create index if not exists timetable_day_idx on public.timetable(day, start_time);
create unique index if not exists timetable_natural_key_idx
  on public.timetable (day, start_time, end_time, room_id, section, subject_id, faculty_id);
create unique index if not exists resources_room_name_idx
  on public.resources (room_id, lower(name));

-- This application accesses Supabase through the protected Flask server using the service-role key.
-- Keep the service-role key only in the host's environment variables; never put it in browser JavaScript.
alter table public.profiles enable row level security;
alter table public.rooms enable row level security;
alter table public.resources enable row level security;
alter table public.subjects enable row level security;
alter table public.issues enable row level security;
alter table public.timetable enable row level security;
alter table public.syllabus_progress enable row level security;
alter table public.eco_reports enable row level security;
