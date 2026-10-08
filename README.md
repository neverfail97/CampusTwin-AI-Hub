# CampusTwin AI — Hybrid Chatbot + Render Deployment Guide

This package contains the CampusTwin AI application with the CampusConnect and EcoCampus experiences, the existing Flask/Supabase APIs, and a **hybrid chatbot**.

## What the hybrid chatbot does

The chatbot has two layers:

1. **Built-in application knowledge/action layer**
   - Runs without an AI API key.
   - Handles common, deterministic questions about the actual CampusTwin features.
   - Gives exact steps for common actions such as adding a room, reporting an issue, using the optimizer, checking the dashboard, investigating EcoCampus anomalies, and using the What-If Simulator.
   - Keeps answers tied to the current product rather than inventing features.

2. **Optional AI layer**
   - Used when the built-in layer does not have a direct answer.
   - The browser sends the question only to your Flask backend.
   - The backend sends the question plus controlled application context to the AI provider.
   - The API key is kept on the server and is never placed in `app.js` or HTML.
   - If the AI provider is unavailable, the chatbot falls back to the local knowledge layer instead of becoming unusable.

The implementation uses the OpenAI **Responses API** when `OPENAI_API_KEY` is configured. Do not put an API key in frontend JavaScript.

## Chatbot visibility rules

The three assistants are intentionally scoped to their own main pages:

- **Ask CampusTwin** → CampusTwin main page only.
- **Ask Connect** → CampusConnect main page only.
- **Ask Eco** → EcoCampus main page only.

They are hidden on the other system and on the system's detail/operation pages.

---

# Part A — Download and extract the project

## 1. Download the ZIP

Download the supplied `CampusTwin-AI-Hybrid-v5.zip` file.

## 2. Extract the ZIP

Extract it into a normal project folder. After extraction you should see a folder similar to:

```text
CampusTwin-AI-Deploy/
├── app.py
├── requirements.txt
├── render.yaml
├── .env.example
├── README.md
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── style.css
└── supabase/
    ├── schema.sql
    └── hackathon_seed.sql
```

Do not rename `app.py`, `templates`, or `static` unless you also change the Flask application.

---

# Part B — Set up Supabase

## 3. Create/open your Supabase project

Create a Supabase project if you do not already have one.

## 4. Create the database tables

Open the Supabase SQL Editor.

Run:

```text
supabase/schema.sql
```

If you want the fictional demonstration data included with this project, run this afterwards:

```text
supabase/setup.sql (fresh/demo) or supabase/hackathon_seed.sql (reset + seed)
```

## 5. Copy the Supabase credentials

From the Supabase project settings, obtain:

- Project URL
- Service role key

The service-role key is a **server secret**. Never paste it into HTML, JavaScript, GitHub, or a browser-visible file.

---

# Part C — Test locally first

## 6. Install Python

Use a supported recent Python 3 version.

## 7. Open a terminal inside `CampusTwin-AI-Deploy`

Example:

```bash
cd CampusTwin-AI-Deploy
```

## 8. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\\Scripts\\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 9. Install dependencies

```bash
pip install -r requirements.txt
```

## 10. Create your local environment file

Copy:

```text
.env.example
```

to:

```text
.env
```

Then fill in:

```text
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
FLASK_SECRET_KEY=a_long_random_secret
```

Do **not** commit `.env` to GitHub.

---

# Part D — Configure the hybrid AI chatbot

The chatbot works without an AI key, so you can first test the deterministic layer.

## 11. Run without an AI API key

Leave these variables empty or remove them from `.env`:

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-6-luna
OPENAI_RESPONSES_URL=https://api.openai.com/v1/responses
```

The chatbot will still answer the built-in CampusTwin/CampusConnect/EcoCampus questions.

## 12. Enable the AI fallback

If you want natural-language questions beyond the built-in rules, add your server-side AI API key:

```text
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-6-luna
OPENAI_RESPONSES_URL=https://api.openai.com/v1/responses
```

The key is read by `app.py`. It is **never sent to the browser**.

The frontend calls only:

```text
POST /api/chat
```

The Flask server decides whether to answer locally or call the AI provider.

## 13. Start the local server

```bash
python app.py
```

If your `app.py` does not include a development launcher, use:

```bash
gunicorn app:app
```

Then open the local address shown by your server, normally:

```text
http://127.0.0.1:5000
```

---

# Part E — Test the chatbot

## 14. Test CampusTwin

Open the CampusTwin main page.

You should see:

```text
Ask CampusTwin
```

Ask questions such as:

- What is CampusConnect?
- What is EcoCampus?
- Which system handles rooms?
- Which system handles water monitoring?

Then switch to another system.

The CampusTwin chatbot must disappear.

## 15. Test CampusConnect

Open the CampusConnect main page.

You should see:

```text
Ask Connect
```

Try:

- How do I add a room?
- How do I update a room?
- How does the AI Resource Optimizer work?
- How do I report an issue?
- What should I include in an issue report?
- How does the timetable check clashes?
- What does the dashboard show?

Navigate to a CampusConnect detail page.

The Ask Connect launcher should disappear there.

## 16. Test EcoCampus

Open the EcoCampus main page.

You should see:

```text
Ask Eco
```

Try:

- How do I investigate the Hostel A anomaly?
- How does the maintenance workflow work?
- How does the What-If Simulator work?
- What is Campus Impact?
- How is Eco Score explained?
- What should I include in an EcoCampus report?
- What does the AI forecast do?

Navigate to an EcoCampus detail page.

The Ask Eco launcher should disappear there.

---

# Part F — Upload the project to GitHub

## 17. Create a GitHub repository

Create a new repository for the project.

## 18. Upload the extracted project

Upload the contents of `CampusTwin-AI-Deploy`.

The repository root should contain:

```text
app.py
requirements.txt
render.yaml
templates/
static/
supabase/
```

Do not upload:

```text
.env
.venv/
__pycache__/
```

## 19. Confirm secrets are not in the repository

Before deploying, search the repository for:

```text
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
```

Only `.env.example` should contain placeholder values.

---

# Part G — Deploy to Render

This project already includes `render.yaml` for a Render Blueprint deployment.

## 20. Create the Render deployment

In Render, create a new Blueprint/Web Service from the GitHub repository.

Render reads:

```text
render.yaml
```

The build command is:

```bash
pip install -r requirements.txt
```

The start command is:

```bash
gunicorn app:app
```

## 21. Add the Supabase environment variables

In the Render service environment settings, add:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

`FLASK_SECRET_KEY` is generated by the supplied `render.yaml`.

## 22. Add the AI environment variable

For hybrid AI mode, add:

```text
OPENAI_API_KEY
```

The supplied `render.yaml` already defines:

```text
OPENAI_MODEL=gpt-6-luna
OPENAI_RESPONSES_URL=https://api.openai.com/v1/responses
```

You may change the model later through the Render environment settings.

## 23. Deploy

Start the Render deployment.

Wait until the build completes successfully.

Open the Render-provided website URL.

---

# Part H — Final production test

## 24. Test the three chatbot visibility rules

### CampusTwin

```text
CampusTwin page       → Ask CampusTwin visible
CampusConnect         → hidden
EcoCampus             → hidden
```

### CampusConnect

```text
CampusConnect page    → Ask Connect visible
CampusTwin            → hidden
EcoCampus             → hidden
Connect detail pages  → hidden
```

### EcoCampus

```text
EcoCampus page        → Ask Eco visible
CampusTwin            → hidden
CampusConnect         → hidden
Eco detail pages      → hidden
```

## 25. Test AI fallback

Ask a question that is not one of the fixed local examples, for example:

```text
Why would the dashboard be useful before I open the maintenance workflow?
```

With `OPENAI_API_KEY` configured, the server should use the AI layer when the local knowledge layer has no direct answer.

## 26. Test fallback behaviour

Temporarily remove the AI key from the server environment and restart the application.

The chatbot should still answer supported application questions using the local knowledge layer.

This means an AI-provider outage does not make the basic product help unusable.

---

# Part I — Troubleshooting

## Chatbot does not open

Check the browser console and confirm that `static/app.js` loaded.

Also confirm the launcher is on the correct main page. The launchers are intentionally hidden on detail pages.

## Chatbot opens but AI answers never appear

Check Render environment variables:

```text
OPENAI_API_KEY
OPENAI_MODEL
OPENAI_RESPONSES_URL
```

Then redeploy/restart the service.

The local fallback should still work even when the AI layer is unavailable.

## AI API errors

Check Render logs. Do not put the API key into frontend code to debug it.

The browser should call:

```text
/api/chat
```

It should never call the AI provider directly with a secret key.

## Supabase errors

Check:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

Also confirm that `schema.sql` was executed in the correct Supabase project.

## Changes are not visible after deployment

1. Confirm the latest commit is pushed to GitHub.
2. Confirm Render deployed that commit.
3. Trigger a new deploy if necessary.
4. Hard-refresh the browser.

---

# File responsibilities

```text
app.py
    Flask routes, Supabase access and hybrid /api/chat endpoint

static/app.js
    UI interaction, chatbot launcher visibility and chat requests

static/style.css
    Existing visual themes and chatbot styling

templates/index.html
    CampusTwin/CampusConnect/EcoCampus markup and chatbot UI

render.yaml
    Render deployment configuration

.env.example
    Environment-variable template

supabase/schema.sql
    Database schema

supabase/setup.sql (fresh/demo) or supabase/hackathon_seed.sql (reset + seed)
    Optional fictional demonstration data
```

## Security reminder

Never commit real values for:

```text
SUPABASE_SERVICE_ROLE_KEY
OPENAI_API_KEY
FLASK_SECRET_KEY
```

The service-role and AI keys belong on the server environment only.

## v6 UI, chart, chatbot and maintenance fixes

This revision adds:
- Strict contextual chatbot visibility: CampusTwin bot only on CampusTwin, Connect bot only on the CampusConnect landing view, and Eco bot only on the EcoCampus landing view. All bots are hidden on detail/operation pages and close automatically when navigation changes.
- Context-specific chatbot colors and readable input/message text.
- Hybrid AI explanation controls inside CampusConnect AI Insights, EcoCampus AI Insights, and the AI Resource Optimizer. These controls use the same `/api/chat` hybrid endpoint without opening a chatbot overlay on a detail page.
- More readable metric-detail breakdowns.
- Eco What-If navigation icon and CampusConnect navigation icon refinements.
- A minimal selected-state animation for the Waste chart tab.
- Chart range controls for Date wise, Hour wise, Week wise, Month wise and Year wise, with explicit X/Y axis labels and metric-specific units.
- Maintenance verification workflow: Start repair -> Worker confirms repair complete -> Faculty verifies resolution -> Resolved. Starting repair no longer marks an issue as resolved.


## CampusConnect database and uploads

For a fresh Supabase demo database, run `supabase/setup.sql` once in Supabase SQL Editor. To verify the seed, run `supabase/verify_seed.sql`. The seed includes rooms, normalized room resources, subjects, timetable entries, issues and syllabus progress.

Timetable upload accepts CSV/TSV/XLSX with `day,start_time,end_time,room_number,section,subject_code`. Syllabus upload accepts CSV/TSV/XLSX with `subject_code,week_number,coverage_percent,topics_covered`.


## CampusConnect database repair

For an existing database that already contains duplicated timetable rows, run `supabase/migrate_deduplicate.sql` once. For a fresh/demo database, run `supabase/setup.sql`; it is intentionally destructive for the application tables and seeds deterministic rooms, resources, subjects, timetable, issues and syllabus progress.
