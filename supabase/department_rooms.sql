-- Adds representative rooms for all engineering departments without deleting data.
-- Run after schema.sql. Existing room numbers are updated, not duplicated.
insert into public.rooms
  (room_number, room_name, category, floor, capacity, benches, projector, board, internet, other_resources, status, department)
values
  ('CSE-201', 'Computer Networks Laboratory', 'Laboratory', 'Second Floor', 60, 30, 'Available', 'Whiteboard', 'Available', 'Network racks, switches', 'Available', 'Computer Science and Engineering'),
  ('CSE-202', 'CSE Faculty Room', 'Faculty Room', 'Second Floor', 18, 9, 'Available', 'Whiteboard', 'Available', 'Meeting display', 'Available', 'Computer Science and Engineering'),
  ('ECE-101', 'Electronics Classroom', 'Classroom', 'Ground Floor', 60, 30, 'Available', 'Whiteboard', 'Available', 'Audio system', 'Available', 'Electronics and Communication Engineering'),
  ('ECE-201', 'Communication Systems Lab', 'Laboratory', 'Second Floor', 48, 24, 'Available', 'Whiteboard', 'Available', 'Oscilloscopes, signal generators', 'Available', 'Electronics and Communication Engineering'),
  ('ECE-202', 'ECE Faculty Room', 'Faculty Room', 'Second Floor', 16, 8, 'Not applicable', 'Whiteboard', 'Available', 'Department printer', 'Available', 'Electronics and Communication Engineering'),
  ('EEE-101', 'Electrical Machines Classroom', 'Classroom', 'Ground Floor', 60, 30, 'Available', 'Whiteboard', 'Available', 'Smart display', 'Available', 'Electrical and Electronics Engineering'),
  ('EEE-201', 'Electrical Machines Lab', 'Laboratory', 'Second Floor', 40, 20, 'Available', 'Whiteboard', 'Available', 'Machine test rigs', 'Available', 'Electrical and Electronics Engineering'),
  ('EEE-202', 'EEE Faculty Room', 'Faculty Room', 'Second Floor', 16, 8, 'Not applicable', 'Whiteboard', 'Available', 'Department printer', 'Available', 'Electrical and Electronics Engineering'),
  ('AIDS-101', 'AI and Data Science Classroom', 'Classroom', 'Ground Floor', 60, 30, 'Available', 'Smart Board', 'Available', 'Lecture capture', 'Available', 'Artificial Intelligence and Data Science'),
  ('AIDS-201', 'Machine Learning Laboratory', 'Laboratory', 'Second Floor', 48, 24, 'Available', 'Smart Board', 'Available', 'GPU workstations', 'Available', 'Artificial Intelligence and Data Science'),
  ('AIDS-202', 'AIDS Faculty Room', 'Faculty Room', 'Second Floor', 16, 8, 'Not applicable', 'Whiteboard', 'Available', 'Meeting display', 'Available', 'Artificial Intelligence and Data Science'),
  ('CIV-101', 'Civil Engineering Classroom', 'Classroom', 'Ground Floor', 60, 30, 'Available', 'Whiteboard', 'Available', 'Drawing boards', 'Available', 'Civil Engineering'),
  ('CIV-201', 'Surveying Laboratory', 'Laboratory', 'Second Floor', 40, 20, 'Available', 'Whiteboard', 'Available', 'Survey equipment', 'Available', 'Civil Engineering'),
  ('CIV-202', 'Civil Faculty Room', 'Faculty Room', 'Second Floor', 16, 8, 'Not applicable', 'Whiteboard', 'Available', 'Department printer', 'Available', 'Civil Engineering'),
  ('MECH-101', 'Mechanical Engineering Classroom', 'Classroom', 'Ground Floor', 70, 35, 'Available', 'Whiteboard', 'Available', 'Smart display', 'Available', 'Mechanical Engineering'),
  ('MECH-201', 'Thermal Engineering Laboratory', 'Laboratory', 'Second Floor', 40, 20, 'Available', 'Whiteboard', 'Available', 'Thermal test equipment', 'Available', 'Mechanical Engineering'),
  ('MECH-202', 'Mechanical Faculty Room', 'Faculty Room', 'Second Floor', 16, 8, 'Not applicable', 'Whiteboard', 'Available', 'Meeting display', 'Available', 'Mechanical Engineering'),
  ('CHEM-101', 'Chemical Engineering Classroom', 'Classroom', 'Ground Floor', 60, 30, 'Available', 'Whiteboard', 'Available', 'Smart display', 'Available', 'Chemical Engineering'),
  ('CHEM-201', 'Process Control Laboratory', 'Laboratory', 'Second Floor', 40, 20, 'Available', 'Whiteboard', 'Available', 'Process control rigs', 'Available', 'Chemical Engineering'),
  ('CHEM-202', 'Chemical Faculty Room', 'Faculty Room', 'Second Floor', 16, 8, 'Not applicable', 'Whiteboard', 'Available', 'Department printer', 'Available', 'Chemical Engineering')
on conflict (room_number) do update set
  room_name = excluded.room_name, category = excluded.category, floor = excluded.floor,
  capacity = excluded.capacity, benches = excluded.benches, projector = excluded.projector,
  board = excluded.board, internet = excluded.internet, other_resources = excluded.other_resources,
  status = excluded.status, department = excluded.department;
