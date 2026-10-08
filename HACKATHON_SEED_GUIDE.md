# CampusConnect database setup

## Fresh/demo database

Run `supabase/setup.sql` once in the Supabase SQL Editor. It creates the schema, clears the demo tables, adds uniqueness guards, and seeds deterministic CampusConnect data.

**Important:** `setup.sql` is destructive for the listed application tables. Do not run it on production data you need to preserve.

## Existing database with duplicate timetable rows

Run `supabase/migrate_deduplicate.sql`. It removes exact duplicate timetable/resource rows and creates database-level uniqueness guards so the screenshot-style duplication cannot return.

## Verification

Run `supabase/verify_seed.sql`. It prints row counts and then lists any remaining exact timetable duplicates. The duplicate query should return zero rows.

## Seeded faculty accounts

- Ananya Rao — `ananya.rao@campus.example` — `CSE2026`
- Vikram Shah — `vikram.shah@campus.example` — `CSE2027`
- Meera Iyer — `meera.iyer@campus.example` — `CSE2028`
- Karan Patel — `karan.patel@campus.example` — `CSE2029`

## Upload templates

- `supabase/timetable_template.csv`
- `supabase/syllabus_progress_template.csv`

The web application accepts CSV, TSV, XLSX and XLSM uploads and stores the results in SQL.
