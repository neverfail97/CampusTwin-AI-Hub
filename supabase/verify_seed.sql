select 'profiles' as table_name, count(*) as row_count from public.profiles
union all select 'rooms', count(*) from public.rooms
union all select 'resources', count(*) from public.resources
union all select 'subjects', count(*) from public.subjects
union all select 'timetable', count(*) from public.timetable
union all select 'syllabus_progress', count(*) from public.syllabus_progress
union all select 'issues', count(*) from public.issues
order by table_name;

select day,start_time,end_time,room_id,section,subject_id,faculty_id,count(*) as duplicate_count
from public.timetable
group by day,start_time,end_time,room_id,section,subject_id,faculty_id
having count(*) > 1
order by duplicate_count desc;
