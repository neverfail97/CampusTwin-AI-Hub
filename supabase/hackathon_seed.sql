-- CampusTwin AI hackathon seed

-- DEMO RESET: this file is intentionally destructive. It makes the seed deterministic
-- so re-running it can never create duplicate timetable/resource rows.
truncate table
  public.eco_reports,
  public.syllabus_progress,
  public.timetable,
  public.issues,
  public.resources,
  public.subjects,
  public.rooms,
  public.profiles
  restart identity cascade;

-- Natural-key guards for records that must not be duplicated.
drop index if exists public.timetable_natural_key_idx;
create unique index public.timetable_natural_key_idx
  on public.timetable (day, start_time, end_time, room_id, section, subject_id, faculty_id);
drop index if exists public.resources_room_name_idx;
create unique index public.resources_room_name_idx
  on public.resources (room_id, lower(name));

-- IMPORTANT: This seed is safe to run against older copies of the schema too.
-- Some older schema versions allowed only faculty/worker in profiles_role_check.
-- The application now supports student, faculty and worker, so normalize that
-- constraint before inserting the demo profiles.
alter table if exists public.profiles
  drop constraint if exists profiles_role_check;

alter table if exists public.profiles
  add constraint profiles_role_check
  check (role in ('student', 'faculty', 'worker'));

insert into public.profiles (id, name, email, role, access_code_hash) values
('a1000000-0000-0000-0000-000000000006','Priya Nair','priya.student@campus.example','student',encode(digest('STUDENT2026','sha256'),'hex')),
('a1000000-0000-0000-0000-000000000001','Ananya Rao','ananya.rao@campus.example','faculty',encode(digest('CSE2026','sha256'),'hex')),
('a1000000-0000-0000-0000-000000000002','Vikram Shah','vikram.shah@campus.example','faculty',encode(digest('CSE2027','sha256'),'hex')),
('a1000000-0000-0000-0000-000000000003','Meera Iyer','meera.iyer@campus.example','faculty',encode(digest('CSE2028','sha256'),'hex')),
('a1000000-0000-0000-0000-000000000004','Karan Patel','karan.patel@campus.example','faculty',encode(digest('CSE2029','sha256'),'hex')),
('a1000000-0000-0000-0000-000000000005','Arun Kumar','arun.maintenance@campus.example','worker',encode(digest('WORKER2026','sha256'),'hex'))
on conflict (id) do nothing;

insert into public.rooms (id,room_number,room_name,category,floor,capacity,benches,occupied_seats,projector,board,internet,other_resources,status) values
('b1000000-0000-0000-0000-000000000001','CSE-101','Programming Classroom','Classroom','Ground Floor',60,30,42,'Available','Whiteboard','Available','Air conditioning','Available'),
('b1000000-0000-0000-0000-000000000002','CSE-102','Smart Lecture Hall','Classroom','Ground Floor',100,50,70,'Available','Smart Board','Available','Air conditioning, audio system','Available'),
('b1000000-0000-0000-0000-000000000003','CSE-103','Data Structures Lab','Laboratory','First Floor',60,30,60,'Unavailable','Whiteboard','Available','60 desktop computers','Attention'),
('b1000000-0000-0000-0000-000000000004','CSE-104','Programming Laboratory','Laboratory','First Floor',72,36,50,'Available','Whiteboard','Available','72 desktop computers, UPS','Available'),
('b1000000-0000-0000-0000-000000000005','CSE-105','AI and Data Science Lab','Laboratory','Second Floor',65,32,38,'Available','Smart Board','Available','GPU workstations, server rack','Available'),
('b1000000-0000-0000-0000-000000000006','CSE-106','Networks Laboratory','Laboratory','Second Floor',48,24,24,'Available','Whiteboard','Available','Network racks, servers','Available'),
('b1000000-0000-0000-0000-000000000007','CSE-107','HOD Office','HOD Room','Second Floor',8,4,3,'Not applicable','Whiteboard','Available','Meeting display','Available'),
('b1000000-0000-0000-0000-000000000008','CSE-108','Seminar Hall','Seminar Hall','Second Floor',100,50,99,'Available','Smart Board','Unavailable','Air conditioning, audio system','Attention'),
('b1000000-0000-0000-0000-000000000009','CSE-109','Faculty Collaboration Room','Faculty Room','First Floor',24,12,12,'Available','Whiteboard','Available','Video conferencing','Available'),
('b1000000-0000-0000-0000-000000000010','CSE-110','Department Store','Other','Ground Floor',0,0,0,'Not applicable','Not applicable','Not applicable','Inventory shelves','Empty'),
('b1000000-0000-0000-0000-000000000011','CSE-T01','Gents Toilet','Toilet','Ground Floor',0,0,0,'Not applicable','Not applicable','Not applicable','Sanitation facilities','Available'),
('b1000000-0000-0000-0000-000000000012','CSE-T02','Ladies Toilet','Toilet','First Floor',0,0,0,'Not applicable','Not applicable','Not applicable','Sanitation facilities','Available')
on conflict (id) do nothing;

insert into public.resources (room_id,name,category,total_count,available_count,status) values
('b1000000-0000-0000-0000-000000000001','Projector','AV',1,1,'Available'),
('b1000000-0000-0000-0000-000000000001','Air conditioning','Facilities',1,1,'Available'),
('b1000000-0000-0000-0000-000000000002','Projector','AV',1,1,'Available'),
('b1000000-0000-0000-0000-000000000002','Audio system','AV',1,1,'Available'),
('b1000000-0000-0000-0000-000000000003','Desktop computers','IT',60,60,'Available'),
('b1000000-0000-0000-0000-000000000004','Desktop computers','IT',72,72,'Available'),
('b1000000-0000-0000-0000-000000000004','UPS','Electrical',36,36,'Available'),
('b1000000-0000-0000-0000-000000000005','GPU workstations','AI Lab',30,28,'Limited'),
('b1000000-0000-0000-0000-000000000005','Server rack','Networking',1,1,'Available'),
('b1000000-0000-0000-0000-000000000006','Network racks','Networking',12,12,'Available'),
('b1000000-0000-0000-0000-000000000006','Servers','IT',4,4,'Available'),
('b1000000-0000-0000-0000-000000000007','Meeting display','AV',1,1,'Available'),
('b1000000-0000-0000-0000-000000000008','Projector','AV',1,1,'Available'),
('b1000000-0000-0000-0000-000000000008','Audio system','AV',1,1,'Available'),
('b1000000-0000-0000-0000-000000000009','Video conferencing','AV',1,1,'Available')
on conflict do nothing;

insert into public.subjects (id,code,name,semester,credits,course_category,syllabus_units,faculty_id) values
('c1000000-0000-0000-0000-000000000001','CSUC103','Fundamentals of Computer Organization',1,4,'Professional Core',5,'a1000000-0000-0000-0000-000000000001'),
('c1000000-0000-0000-0000-000000000002','CSUC101','Programming for Problem Solving',1,2,'Engineering Science',5,'a1000000-0000-0000-0000-000000000002'),
('c1000000-0000-0000-0000-000000000003','MAUC101','Mathematics I',1,4,'Basic Science',5,'a1000000-0000-0000-0000-000000000003'),
('c1000000-0000-0000-0000-000000000004','CS301','Data Structures',3,4,'Professional Core',5,'a1000000-0000-0000-0000-000000000002'),
('c1000000-0000-0000-0000-000000000005','CS302','Database Management Systems',3,4,'Professional Core',5,'a1000000-0000-0000-0000-000000000004'),
('c1000000-0000-0000-0000-000000000006','CS303','Computer Networks',3,3,'Professional Core',5,'a1000000-0000-0000-0000-000000000003'),
('c1000000-0000-0000-0000-000000000007','CS401','Artificial Intelligence',4,4,'Professional Core',5,'a1000000-0000-0000-0000-000000000001')
on conflict (id) do nothing;

insert into public.timetable (day,day_order,start_time,end_time,room_id,section,subject_id,faculty_id) values
('Monday',1,'09:00','09:50','b1000000-0000-0000-0000-000000000001','CSE-A','c1000000-0000-0000-0000-000000000004','a1000000-0000-0000-0000-000000000002'),
('Monday',1,'09:50','10:40','b1000000-0000-0000-0000-000000000004','CSE-A','c1000000-0000-0000-0000-000000000005','a1000000-0000-0000-0000-000000000004'),
('Tuesday',2,'10:50','11:40','b1000000-0000-0000-0000-000000000005','CSE-B','c1000000-0000-0000-0000-000000000007','a1000000-0000-0000-0000-000000000001'),
('Wednesday',3,'11:40','12:30','b1000000-0000-0000-0000-000000000006','CSE-B','c1000000-0000-0000-0000-000000000006','a1000000-0000-0000-0000-000000000003'),
('Thursday',4,'13:30','14:20','b1000000-0000-0000-0000-000000000003','CS1-A','c1000000-0000-0000-0000-000000000002','a1000000-0000-0000-0000-000000000002'),
('Friday',5,'14:20','15:10','b1000000-0000-0000-0000-000000000001','CS1-A','c1000000-0000-0000-0000-000000000001','a1000000-0000-0000-0000-000000000001')
on conflict do nothing;

insert into public.issues (room_id,title,category,priority,priority_rank,description,status,reported_by,assigned_to,worker_note,faculty_verification) values
('b1000000-0000-0000-0000-000000000003','Projector has no display','Projector','Critical',4,'The projector powers on but does not produce an image during scheduled laboratory sessions.','In Progress','a1000000-0000-0000-0000-000000000002','a1000000-0000-0000-0000-000000000005','Lamp assembly inspection is in progress.','Pending'),
('b1000000-0000-0000-0000-000000000008','Network connection unavailable','Network','High',3,'The seminar hall network is not reachable for scheduled presentations.','Open','a1000000-0000-0000-0000-000000000001',null,'','Pending'),
('b1000000-0000-0000-0000-000000000011','Wash basin tap leak','Sanitation','Medium',2,'A slow water leak is visible at the wash basin.','Resolved','a1000000-0000-0000-0000-000000000003','a1000000-0000-0000-0000-000000000005','Washer replaced; awaiting faculty verification.','Pending')
on conflict do nothing;

insert into public.syllabus_progress (subject_id,week_number,coverage_percent,topics_covered,updated_by) values
('c1000000-0000-0000-0000-000000000004',8,72,'Arrays, linked lists, stacks and queues completed.','a1000000-0000-0000-0000-000000000002'),
('c1000000-0000-0000-0000-000000000005',8,61,'ER modelling, relational algebra and SQL foundations completed.','a1000000-0000-0000-0000-000000000004'),
('c1000000-0000-0000-0000-000000000006',8,80,'Network models, physical layer and data link layer completed.','a1000000-0000-0000-0000-000000000003'),
('c1000000-0000-0000-0000-000000000007',8,48,'Intelligent agents and uninformed search completed.','a1000000-0000-0000-0000-000000000001'),
('c1000000-0000-0000-0000-000000000001',8,55,'Number systems, Boolean algebra and processor basics completed.','a1000000-0000-0000-0000-000000000001'),
('c1000000-0000-0000-0000-000000000002',8,68,'Problem decomposition, algorithms and C programming fundamentals completed.','a1000000-0000-0000-0000-000000000002')
on conflict (subject_id, week_number) do update set coverage_percent=excluded.coverage_percent, topics_covered=excluded.topics_covered, updated_by=excluded.updated_by, updated_at=now();


insert into public.eco_reports (email,location,category,description,photo_name,status) values
('student01@campus.example','Hostel A','💧 Water leak','Water continues to flow near the Block A wash area after 6:30 PM; possible plumbing leak.','hostel-a-leak.jpg','Assigned'),
('student02@campus.example','Academic Block','💡 Energy waste','Several rooms show unusually high cooling demand between 2 PM and 4 PM; please check HVAC schedules.','hvac-panel.jpg','In Progress'),
('student03@campus.example','Cafeteria','🗑 Waste problem','Cafeteria collection bin is nearly full before the planned pickup window.','cafeteria-bin.jpg','Resolved')
on conflict do nothing;
