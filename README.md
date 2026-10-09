# CampusTwin AI — online and Supabase-ready

This package keeps **Project 1** as the application base and adds the missing deployment, Supabase, dependency, and security configuration from the CampusTwin archive.

## Included changes

- `requirements.txt` now includes the server libraries required by `app.py`: Supabase, Google GenAI, and Gunicorn.
- `supabase/schema.sql` creates the application tables, enables RLS, and includes the profile, room-occupancy, and Eco-report fields used by the Project 1 backend.
- `supabase/setup.sql` is the optional destructive demo reset/seed from the additional archive. Do not run it on real data.
- `render.yaml` deploys the Flask app as a Render web service, listening on Render's `$PORT`.
- `.env.example` documents server-only configuration without exposing secrets.

## Run locally

1. Create a Supabase project.
2. In its SQL Editor, run `supabase/schema.sql`, then `supabase/department_rooms.sql` to add rooms for all seven engineering departments. For sample data only, run `supabase/setup.sql` beforehand; it deletes the app tables first.
3. Copy `.env.example` to `.env` and fill in your project URL, server secret/service-role key, and a long Flask secret.
4. Create a virtual environment, install dependencies, then start the app:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
   ```

5. Browse to `http://127.0.0.1:5000`.

## Deploy online with Render

Push this folder to a Git repository, then create a Render Blueprint or web service. `render.yaml` installs dependencies and starts Gunicorn. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in Render; never commit them. Render generates `FLASK_SECRET_KEY` and enables secure session cookies.

The app accesses Supabase only from Flask using its server-side key. Browser files contain no Supabase or AI credentials. RLS remains enabled on every exposed table.
