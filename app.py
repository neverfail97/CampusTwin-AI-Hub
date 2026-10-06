"""Server-side API for Smart Campus Management using Supabase PostgreSQL."""
from __future__ import annotations

import hashlib
import os
import json
import csv
import io
import urllib.error
import urllib.request
try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from supabase import create_client

load_dotenv()
app = Flask(__name__, static_folder="static")
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
)

url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key) if url and key else None


def now(): return datetime.now(timezone.utc).isoformat()
def code_hash(value): return hashlib.sha256(value.strip().encode()).hexdigest()
def error(message, status=400): return jsonify({"error": message}), status
def client():
    if not supabase: raise RuntimeError("Supabase is not configured. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to .env.")
    return supabase
def signed_in(role=None):
    profile = session.get("profile")
    if not profile: return None
    return profile if not role or profile["role"] == role else None
def require(role=None, roles=None):
    profile = signed_in()
    allowed = set(roles or ([role] if role else []))
    if not profile:
        return None
    if allowed and profile["role"] not in allowed:
        return None
    return profile



CHAT_KNOWLEDGE = {
    "twin": {
        "name": "CampusTwin AI Guide",
        "scope": "CampusTwin AI overview page only.",
        "topics": "CampusConnect academic operations, EcoCampus sustainability operations, navigation between the two systems, and which system handles a task.",
    },
    "connect": {
        "name": "CampusConnect Assistant",
        "scope": "CampusConnect main page only. Explain Rooms & Resources, AI Resource Optimizer, Maintenance Desk, Timetable, Syllabus Progress, Dashboard, Room Map, AI Insights and Report Issue.",
        "topics": "Rooms can be added or edited through the room pop-up. Dashboard covers room availability, occupancy, issues and syllabus coverage. Room Map supports room selection and details. Maintenance follows issue reporting and repair/verification. Timetable checks clashes. Syllabus records coverage.",
    },
    "eco": {
        "name": "EcoCampus Advisor",
        "scope": "EcoCampus main page only. Explain dashboard, campus map, resources, AI insights, maintenance operations, impact, what-if simulator, building profiles, Eco Score and reporting.",
        "topics": "EcoCampus action loop is Measure -> Detect -> Explain -> Act -> Verify -> Save. Hostel A has a water anomaly example. The What-If Simulator produces projections, not measured savings. Building profiles show water, energy, waste, occupancy, alerts and recommendations.",
    },
}

LOCAL_CHAT_RULES = {
    "twin": [
        (lambda q: any(x in q for x in ("campusconnect", "connect")), "CampusConnect is the academic-operations side: rooms and resources, AI Resource Optimizer, maintenance, clash-free timetable and syllabus progress."),
        (lambda q: any(x in q for x in ("ecocampus", "eco campus", "water", "energy", "waste", "sustainability")), "EcoCampus is the sustainability side: water, energy and waste monitoring, Eco Score, campus map, AI insights, maintenance actions, impact and issue reporting."),
        (lambda q: "navigate" in q or "where" in q or "how do i use" in q, "Use the main CampusTwin switcher to enter CampusConnect or EcoCampus. Each system keeps its own dashboard, operations and reporting workflows."),
    ],
    "connect": [
        (lambda q: "add" in q and "room" in q, "Open Operations → Rooms & resources → Add room. Fill the room pop-up, then press Add room. The browser prompt/alert is not used for room entry."),
        (lambda q: any(x in q for x in ("update room", "edit room", "change room")), "Open Operations → Rooms & resources, find the room, and use its Edit action. Update the fields in the same pop-up and save."),
        (lambda q: any(x in q for x in ("optimizer", "best room", "recommend room")), "Open AI Resource Optimizer. Enter student count, day/time and required equipment. It evaluates capacity, status, timetable conflicts, maintenance issues and equipment availability."),
        (lambda q: any(x in q for x in ("maintenance", "repair", "issue queue")), "Open Maintenance desk to review active issues. Issues move through reporting, assignment, In Progress/Resolved repair updates and faculty verification."),
        (lambda q: "report" in q and any(x in q for x in ("include", "content", "write", "what should")), "A strong report should include the room, exact problem/equipment, when it started, impact on teaching, priority and requested action. Example: CSE-103 projector not displaying input during class; observed at 10:15; teaching blocked; High priority; inspect projector and cable."),
        (lambda q: "report" in q or "complaint" in q, "Open Report issue. Enter faculty email, room, priority and a clear description, then submit."),
        (lambda q: any(x in q for x in ("timetable", "clash", "schedule")), "Open Clash-free timetable. Enter day, section, start/end time, room and subject. The system checks overlapping room bookings before saving."),
        (lambda q: any(x in q for x in ("syllabus", "coverage", "progress")), "Open Syllabus progress. Record subject code, week, coverage percentage, credits and topics covered, then save the weekly update."),
        (lambda q: any(x in q for x in ("dashboard", "occupancy")), "CampusConnect Dashboard summarizes rooms available, seat occupancy, open issues and syllabus coverage. Chart tabs switch between Occupancy, Issues and Coverage."),
        (lambda q: "room map" in q or ("map" in q and "room" in q), "Room Map lets you choose a room from the selector or click a map block. The detail panel shows capacity, occupancy, equipment, status and the recommended action."),
    ],
    "eco": [
        (lambda q: "hostel" in q and any(x in q for x in ("anomaly", "water", "investigate")), "Open AI Insights and choose the Hostel A water anomaly. Investigate it to see current usage, expected baseline, deviation, detected pattern, possible causes, confidence and the recommended action. Then create a maintenance ticket."),
        (lambda q: any(x in q for x in ("what-if", "what if", "simulator", "simulate improvement")), "The What-If Simulator lets you adjust projected reductions for water, energy and waste. It calculates projected monthly impact and clearly treats those values as projections, not measured savings."),
        (lambda q: any(x in q for x in ("maintenance", "active issue", "assign", "in progress", "resolved")), "EcoCampus Maintenance Command Center follows Detect → Assign → In progress → Resolved. After simulated repair, the system can show verification and estimated savings."),
        (lambda q: any(x in q for x in ("impact", "saving", "savings")), "Campus Impact summarizes this month's estimated water saved, energy saved, waste diverted, CO₂ reduction and cost avoided, with trend information."),
        (lambda q: "eco score" in q or "score" in q, "Eco Score is transparent: review water efficiency, energy efficiency, waste management and issue response rather than treating the score as an unexplained AI number."),
        (lambda q: any(x in q for x in ("building profile", "hostel a profile", "building")), "A building profile can show Eco Score, water, energy, waste, occupancy, active alerts and an AI recommendation. Select a building from the campus map to inspect it."),
        (lambda q: "forecast" in q or "prediction" in q or "predict" in q, "The AI Forecast card provides a forward-looking signal, such as projected energy demand peaks, plus a recommended preparation action."),
        (lambda q: "report" in q and any(x in q for x in ("include", "content", "what should", "write")), "For an EcoCampus report, choose a quick category such as Water leak, Energy waste, Waste problem, HVAC issue or Other, then provide the location, what you observed, a useful description and any available photo. The system returns a ticket and status."),
        (lambda q: "report" in q or "complaint" in q, "Open Report Issue, choose the category, location and description, attach a photo if available, and submit. The resulting ticket can enter the maintenance workflow."),
        (lambda q: any(x in q for x in ("dashboard", "water", "energy", "waste")), "EcoCampus Dashboard monitors water, energy and waste against baselines and shows Eco Score and resource signals. Use an anomaly's action control to move from detection into investigation and maintenance."),
    ],
}

def local_chat_answer(mode, question):
    q = " ".join(question.lower().strip().split())
    for matcher, answer in LOCAL_CHAT_RULES.get(mode, []):
        if matcher(q):
            return answer
    return None

def chat_context(mode, page):
    base = CHAT_KNOWLEDGE.get(mode, CHAT_KNOWLEDGE["twin"])
    return f"Assistant: {base['name']}\nScope: {base['scope']}\nCurrent page: {page or 'main page'}\nProduct knowledge: {base['topics']}"

def call_ai_chat(mode, page, question, history):
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.environ.get("OPENAI_MODEL", "gpt-6-luna").strip()
    endpoint = os.environ.get("OPENAI_RESPONSES_URL", "https://api.openai.com/v1/responses").strip()
    instructions = (
        "You are a helpful in-product assistant for CampusTwin AI. Answer only about the application's documented features. "
        "Do not invent buttons, data, APIs, permissions or capabilities. If the user asks how to perform an action, give short numbered steps. "
        "Distinguish measured values from projected/simulated values. Never reveal or request secret API keys. "
        + chat_context(mode, page)
    )
    recent = []
    for item in (history or [])[-8:]:
        role = item.get("role") if isinstance(item, dict) else None
        content = item.get("content") if isinstance(item, dict) else None
        if role in ("user", "assistant") and isinstance(content, str):
            recent.append({"role": role, "content": content[:2000]})
    recent.append({"role": "user", "content": question[:4000]})
    payload = {"model": model, "instructions": instructions, "input": recent, "max_output_tokens": 500}
    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
        if isinstance(data.get("output_text"), str) and data["output_text"].strip():
            return data["output_text"].strip()
        texts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    texts.append(content["text"])
        return "\n".join(texts).strip() or None
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

@app.post("/api/chat")
def chat():
    if not require(roles=["student", "faculty", "worker"]):
        return error("Sign in to use the CampusTwin assistant.", 401)
    data = request.get_json() or {}
    mode = data.get("mode", "twin") if data.get("mode") in CHAT_KNOWLEDGE else "twin"
    page = str(data.get("page", "main"))[:100]
    question = str(data.get("question", "")).strip()
    if not question:
        return error("Enter a question.")
    local = local_chat_answer(mode, question)
    if local:
        return jsonify({"answer": local, "source": "local"})
    ai = call_ai_chat(mode, page, question, data.get("history", []))
    if ai:
        return jsonify({"answer": ai, "source": "ai"})
    fallback = {
        "twin": "I can explain CampusConnect, EcoCampus, navigation and what each system is used for. Ask me about one of those features.",
        "connect": "I can help with Rooms & Resources, the Optimizer, Maintenance, Timetable, Syllabus Progress, Dashboard, Room Map, AI Insights and reporting. Ask me how to use a specific feature.",
        "eco": "I can help with the EcoCampus dashboard, anomalies, maintenance workflow, What-If Simulator, building profiles, Eco Score, Campus Impact and issue reporting.",
    }[mode]
    return jsonify({"answer": fallback, "source": "local-fallback"})

@app.errorhandler(RuntimeError)
def config_error(exc): return error(str(exc), 503)

@app.get("/")
def home(): return send_from_directory("templates", "index.html")

@app.get("/api/session")
def get_session(): return jsonify({"profile": session.get("profile")})

@app.post("/api/session")
def sign_in():
    """Authenticate an existing seeded/administratively-created faculty or worker profile."""
    data = request.get_json() or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    access_code = str(data.get("access_code", "")).strip()
    role = str(data.get("role", "faculty")).strip().lower()
    if not email or "@" not in email or role not in ("student", "faculty", "worker"):
        return error("Choose Student, Faculty or Worker and enter a valid college email.")
    if role in ("faculty", "worker") and (not name or not access_code):
        return error("Faculty and Worker sign-in requires name and access code.")
    if role == "student" and not name:
        return error("Student sign-in requires your registered name.")
    db = client()
    existing = db.table("profiles").select("*").eq("email", email).eq("role", role).limit(1).execute().data
    if not existing:
        return error("No matching account exists. Ask the administrator to add your college profile.", 401)
    profile = existing[0]
    if profile["name"].casefold() != name.casefold():
        return error("The supplied name or role is incorrect.", 403)
    if role in ("faculty", "worker") and profile["access_code_hash"] != code_hash(access_code):
        return error("The supplied access code is incorrect.", 403)
    session["profile"] = {"id": profile["id"], "name": profile["name"], "email": profile["email"], "role": profile["role"]}
    return jsonify({"profile": session["profile"]})

@app.delete("/api/session")
def sign_out(): session.clear(); return jsonify({"message": "Signed out."})

@app.post("/api/eco-reports")
def create_eco_report():
    profile = require(roles=["student", "faculty", "worker"])
    if not profile:
        return error("Sign in before submitting an EcoCampus report.", 401)
    data = request.get_json() or {}
    email = str(data.get("email", "")).strip().lower()
    location = str(data.get("location", "")).strip()
    category = str(data.get("category", "")).strip()
    description = str(data.get("description", "")).strip()
    photo_name = str(data.get("photo_name", "")).strip()
    if not email or "@" not in email or not location or not category or not description:
        return error("Enter a valid college email, location, category and description.")
    if email != profile["email"]:
        return error("Use the college email associated with the signed-in account.", 403)
    row = client().table("eco_reports").insert({
        "email": email, "location": location, "category": category,
        "description": description, "photo_name": photo_name, "status": "Assigned",
        "created_at": now()
    }).execute().data[0]
    return jsonify({"ticket": f"EC-{str(row['id'])[:8].upper()}", "report": row}), 201

@app.get("/api/dashboard")
def dashboard():
    if not require(roles=["faculty", "worker"]): return error("You do not have access to CampusConnect dashboard.", 403)
    db = client(); rooms = db.table("rooms").select("capacity, benches, occupied_seats, status").execute().data
    issues = db.table("issues").select("id").neq("status", "Verified").execute().data
    return jsonify({"rooms": len(rooms), "available": sum(x["status"] == "Available" for x in rooms), "attention": sum(x["status"] == "Attention" for x in rooms), "empty": sum(x["status"] == "Empty" for x in rooms), "unavailable": sum(x["status"] == "Unavailable" for x in rooms), "benches": sum(x["benches"] for x in rooms), "seats": sum(x["capacity"] for x in rooms), "occupied": sum(x["occupied_seats"] for x in rooms), "open_issues": len(issues)})

def _room_records(category="", term=""):
    """Load rooms and their resources without relying on a PostgREST relationship cache.

    Supabase can temporarily report an embedded-relation error when the `resources`
    foreign key was created/changed after the API schema cache was refreshed. Loading
    the two tables separately keeps the CampusConnect page usable while preserving the
    SQL-backed source of truth.
    """
    db = client()
    query = db.table("rooms").select("*").order("room_number")
    if category:
        query = query.eq("category", category)
    data = query.execute().data or []
    if term:
        needle = term.casefold()
        data = [r for r in data if needle in f"{r.get('room_number','')} {r.get('room_name','')}".casefold()]
    if not data:
        return []
    try:
        room_ids = [r["id"] for r in data]
        resource_rows = db.table("resources").select("*").in_("room_id", room_ids).order("name").execute().data or []
    except Exception:
        resource_rows = []
    grouped = {rid: [] for rid in [r["id"] for r in data]}
    for resource in resource_rows:
        grouped.setdefault(resource.get("room_id"), []).append(resource)
    for room in data:
        room["resources"] = grouped.get(room["id"], [])
    return data

@app.get("/api/rooms")
def rooms():
    if not require(roles=["faculty", "worker"]): return error("You do not have access to CampusConnect rooms.", 403)
    try:
        return jsonify(_room_records(request.args.get("category", ""), request.args.get("q", "")))
    except Exception as exc:
        return error(f"Rooms could not be loaded from SQL: {exc}", 503)

@app.get("/api/resources")
def resources():
    if not require(roles=["faculty", "worker"]): return error("You do not have access to CampusConnect resources.", 403)
    try:
        data = client().table("resources").select("*").order("name").execute().data or []
        room_ids = list({r.get("room_id") for r in data if r.get("room_id")})
        rooms_by_id = {}
        if room_ids:
            for room in client().table("rooms").select("id,room_number,room_name").in_("id", room_ids).execute().data or []:
                rooms_by_id[room["id"]] = room
        for item in data:
            item["rooms"] = rooms_by_id.get(item.get("room_id"))
        return jsonify(data)
    except Exception as exc:
        return error(f"Resources could not be loaded from SQL: {exc}", 503)

@app.post("/api/rooms")
def add_room():
    profile = require("faculty")
    if not profile:
        return error("Sign in as faculty to add or edit rooms.", 401)
    data = request.get_json() or {}
    fields = ("room_number", "room_name", "category", "floor", "capacity", "benches",
              "occupied_seats", "projector", "board", "internet", "other_resources", "status")
    if not all(str(data.get(k, "")).strip() for k in fields):
        return error("Complete all room fields.")
    try:
        capacity = int(data["capacity"]); benches = int(data["benches"]); occupied = int(data["occupied_seats"])
    except (TypeError, ValueError):
        return error("Capacity, benches and occupied seats must be whole numbers.")
    if min(capacity, benches, occupied) < 0 or occupied > capacity:
        return error("Occupied seats must be between 0 and room capacity.")
    allowed_categories = {"Classroom","Laboratory","Staff Room","HOD Room","Faculty Room","Seminar Hall","Toilet","Other"}
    allowed_status = {"Available","Attention","Unavailable","Empty"}
    if data["category"] not in allowed_categories or data["status"] not in allowed_status:
        return error("Invalid room category or status.")
    payload = {**{k: data[k] for k in fields}, "capacity": capacity, "benches": benches, "occupied_seats": occupied}
    try:
        row = client().table("rooms").insert(payload).execute().data[0]
    except Exception as exc:
        return error("Room could not be saved. Check the room number and database constraints.", 409)
    return jsonify(row), 201

@app.patch("/api/rooms/<room_id>")
def update_room(room_id):
    profile = require("faculty")
    if not profile:
        return error("Sign in as faculty to add or edit rooms.", 401)
    data = request.get_json() or {}
    allowed = ("room_number", "room_name", "category", "floor", "capacity", "benches",
               "occupied_seats", "projector", "board", "internet", "other_resources", "status")
    payload = {k: data[k] for k in allowed if k in data}
    if not payload:
        return error("No room changes supplied.")
    for k in ("capacity", "benches", "occupied_seats"):
        if k in payload:
            try: payload[k] = int(payload[k])
            except (TypeError, ValueError): return error("Capacity, benches and occupied seats must be whole numbers.")
    if any(k in payload and payload[k] < 0 for k in ("capacity","benches","occupied_seats")):
        return error("Room counts cannot be negative.")
    if "capacity" in payload and "occupied_seats" in payload and payload["occupied_seats"] > payload["capacity"]:
        return error("Occupied seats cannot exceed capacity.")
    try:
        row = client().table("rooms").update(payload).eq("id", room_id).execute().data
    except Exception:
        return error("Room could not be updated. Check the room number and database constraints.", 409)
    if not row:
        return error("Room not found.", 404)
    return jsonify(row[0])

@app.post("/api/optimizer")
@app.post("/api/optimize-resources")
def optimize_room():
    """Constraint-based campus resource recommendation with explainable scoring."""
    profile = require("faculty")
    if not profile:
        return error("Sign in as faculty to use the AI Resource Optimizer.", 401)
    data = request.get_json() or {}
    try:
        students = int(data.get("students", 0))
    except (TypeError, ValueError):
        return error("Student count must be a positive number.")
    day, start_time, end_time = data.get("day"), data.get("start_time"), data.get("end_time")
    if students < 1 or not day or not start_time or not end_time or start_time >= end_time:
        return error("Enter a day, valid time range, and student count.")

    db = client()
    rooms_data = db.table("rooms").select("*").execute().data
    entries = db.table("timetable").select("room_id,start_time,end_time,section,faculty_id").eq("day", day).execute().data
    issues_data = [issue for issue in db.table("issues").select("room_id,title,status,priority").execute().data if issue["status"] not in ("Resolved", "Verified") ]
    active_issues = {}
    for issue in issues_data:
        active_issues.setdefault(issue["room_id"], []).append(issue)
    recommendations, rejected = [], []

    for room in rooms_data:
        reasons = []
        conflicts = [entry for entry in entries if entry["room_id"] == room["id"] and entry["start_time"] < end_time and entry["end_time"] > start_time]
        if room["status"] != "Available": reasons.append(f"room status is {room['status'].lower()}")
        if room["capacity"] < students: reasons.append(f"capacity is {room['capacity']}, below the required {students}")
        if data.get("projector") and room["projector"] != "Available": reasons.append("projector is unavailable")
        if data.get("network") and room["internet"] != "Available": reasons.append("network is unavailable")
        if data.get("board") and room["board"] not in ("Available", "Whiteboard", "Smart Board"): reasons.append("board is unavailable")
        if conflicts: reasons.append("has a timetable conflict")
        if active_issues.get(room["id"]): reasons.append("has an unresolved maintenance issue")
        if reasons:
            rejected.append({"room_number": room["room_number"], "room_name": room["room_name"], "reasons": reasons})
            continue
        spare = room["capacity"] - students
        score = 100 - min(spare, 60) * 0.45 - min(room["occupied_seats"], 80) * 0.05
        if room["category"] == "Classroom":
            score += 15  # Prefer teaching-ready classroom space over a laboratory when both fit.
        suitability = [f"{room['capacity']} seats for {students} students", "Available status", "no timetable conflict"]
        if data.get("projector"): suitability.append("projector available")
        if data.get("network"): suitability.append("network available")
        if data.get("board"): suitability.append("board available")
        if room["category"] == "Classroom": suitability.append("teaching-ready classroom setting")
        recommendations.append({"room_id":room["id"], "room_number":room["room_number"], "room_name":room["room_name"], "category":room["category"], "capacity":room["capacity"], "occupied_seats":room["occupied_seats"], "score":round(max(score, 0), 1), "reasons":suitability})
    recommendations.sort(key=lambda room: room["score"], reverse=True)
    return jsonify({"recommendations": recommendations[:3], "rejected": rejected[:5], "analysis": f"Evaluated {len(rooms_data)} campus spaces against capacity, equipment, status, maintenance and timetable constraints."})

@app.get("/api/issues")
def issues():
    if not require(roles=["faculty", "worker"]): return error("You do not have access to the maintenance queue.", 403)
    return jsonify(client().table("issues").select("*, rooms(room_number,room_name)").order("priority_rank", desc=True).order("created_at", desc=True).execute().data)

@app.post("/api/issues")
def report_issue():
    profile = require("faculty")
    if not profile: return error("Sign in as faculty to report an issue.", 401)
    data = request.get_json() or {}
    required = ("room_id", "title", "category", "priority", "description")
    if not all(data.get(field) for field in required): return error("Complete all issue fields.")
    rank = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}.get(data["priority"], 1)
    result = client().table("issues").insert({**{k:data[k] for k in required}, "priority_rank":rank, "reported_by":profile["id"], "created_at":now()}).execute().data
    return jsonify(result[0]), 201

@app.patch("/api/issues/<issue_id>/repair")
def repair(issue_id):
    profile = require("worker")
    if not profile: return error("Sign in as maintenance staff to update this issue.", 401)
    data = request.get_json() or {}; status = data.get("status")
    if status not in ("In Progress", "Resolved"): return error("Choose In Progress or Resolved.")
    client().table("issues").update({"status":status,"worker_note":data.get("worker_note", ""),"updated_at":now(),"assigned_to":profile["id"]}).eq("id", issue_id).execute()
    return jsonify({"message":"Maintenance update saved."})

@app.patch("/api/issues/<issue_id>/verify")
def verify(issue_id):
    profile = require("faculty")
    if not profile: return error("Sign in as faculty to verify this issue.", 401)
    data = request.get_json() or {}; verdict = data.get("verdict")
    issue = client().table("issues").select("reported_by").eq("id", issue_id).execute().data
    if not issue: return error("Issue not found.", 404)
    if issue[0]["reported_by"] != profile["id"]: return error("Only the reporting faculty member may verify or reopen this issue.", 403)
    if verdict not in ("Verified", "Reopened"): return error("Choose Verified or Reopened.")
    client().table("issues").update({"status":"Verified" if verdict == "Verified" else "Open", "faculty_verification":verdict, "updated_at":now()}).eq("id", issue_id).execute()
    return jsonify({"message":f"Issue {verdict.lower()}."})

@app.get("/api/subjects")
def subjects():
    if not require("faculty"): return error("You do not have access to subjects.", 403)
    return jsonify(client().table("subjects").select("*, profiles(name)").order("semester").order("code").execute().data)

@app.patch("/api/syllabus/catalog/<subject_id>")
def update_syllabus_catalog(subject_id):
    profile=require("faculty")
    if not profile:return error("Sign in as faculty to edit syllabus records.",401)
    existing=client().table("subjects").select("*").eq("id",subject_id).limit(1).execute().data
    if not existing:return error("Syllabus course not found.",404)
    row=existing[0]; data=request.get_json() or {}
    code=str(data.get("code",row.get("code",""))).strip()
    name=str(data.get("name",row.get("name",""))).strip()
    category=str(data.get("course_category",row.get("course_category","Core"))).strip() or "Core"
    try: semester=int(data.get("semester",row.get("semester"))); credits=float(data.get("credits",row.get("credits"))); units=int(data.get("syllabus_units",row.get("syllabus_units")))
    except (TypeError,ValueError): return error("Semester, credits and syllabus units must be numeric.")
    if not code or not name or not 1<=semester<=8 or credits<=0 or units<=0:return error("Complete the syllabus course fields.")
    clash=client().table("subjects").select("id").eq("code",code).neq("id",subject_id).limit(1).execute().data
    if clash:return error("Another course already uses that code.",409)
    output=client().table("subjects").update({"code":code,"name":name,"semester":semester,"credits":credits,"course_category":category,"syllabus_units":units}).eq("id",subject_id).select("*").execute().data
    if not output: return error("The syllabus update was not persisted. Refresh and try again.",500)
    return jsonify(output[0])

@app.delete("/api/syllabus/catalog/<subject_id>")
def delete_syllabus_catalog(subject_id):
    profile=require("faculty")
    if not profile:return error("Sign in as faculty to delete syllabus records.",401)
    existing=client().table("subjects").select("id").eq("id",subject_id).limit(1).execute().data
    if not existing:return error("Syllabus course not found.",404)
    linked_t=client().table("timetable").select("id").eq("subject_id",subject_id).limit(1).execute().data
    linked_p=client().table("syllabus_progress").select("id").eq("subject_id",subject_id).limit(1).execute().data
    if linked_t or linked_p:return error("This course is linked to timetable/progress data, so delete its linked records first.",409)
    client().table("subjects").delete().eq("id",subject_id).execute()
    return jsonify({"message":"Syllabus course deleted."})


def _read_upload_rows(upload):
    """Read CSV/TSV/XLSX uploads into normalized dictionaries."""
    if not upload or not upload.filename:
        raise ValueError("Choose a CSV, TSV or XLSX file.")
    name = upload.filename.lower()
    raw = upload.read()
    if name.endswith((".xlsx", ".xlsm")):
        if load_workbook is None:
            raise ValueError("XLSX support is not installed. Run pip install -r requirements.txt.")
        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        if not rows: return []
        headers = [str(x or "").strip().lower().replace(" ", "_") for x in rows[0]]
        return [dict(zip(headers, ["" if v is None else str(v).strip() for v in row])) for row in rows[1:] if any(v is not None and str(v).strip() for v in row)]
    text = raw.decode("utf-8-sig")
    sample = text[:4096]
    dialect = csv.Sniffer().sniff(sample, delimiters=",\t;") if sample.strip() else csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    return [{str(k or "").strip().lower().replace(" ", "_"): str(v or "").strip() for k, v in row.items()} for row in reader if any(str(v or "").strip() for v in row.values())]


def _time_value(value):
    """Normalize common time inputs to HH:MM for comparisons and inserts."""
    value = str(value or "").strip()
    if not value:
        return ""
    # Accept HH:MM, H:MM and HH:MM:SS.
    parts = value.split(":")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        hour, minute = int(parts[0]), int(parts[1])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"
    return value


def _minutes(value):
    """Return minutes since midnight, or None for an invalid time."""
    normalized = _time_value(value)
    if len(normalized) != 5 or normalized[2] != ":":
        return None
    try:
        hour, minute = int(normalized[:2]), int(normalized[3:])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour * 60 + minute


def _timetable_conflict(entry, day, start_time, end_time, room_id, section, faculty_id, exclude_id=None):
    """Return True when a timetable row overlaps on room, section, or lecturer."""
    if entry.get("day") != day or (exclude_id and str(entry.get("id")) == str(exclude_id)):
        return False
    start = _minutes(entry.get("start_time"))
    end = _minutes(entry.get("end_time"))
    new_start = _minutes(start_time)
    new_end = _minutes(end_time)
    if None in (start, end, new_start, new_end):
        return False
    overlaps = start < new_end and end > new_start
    same_resource = (entry.get("room_id") == room_id or
                     entry.get("section") == section or
                     entry.get("faculty_id") == faculty_id)
    return overlaps and same_resource

@app.get("/api/timetable")
def timetable():
    if not require("faculty"): return error("You do not have access to the timetable.", 403)
    rows = client().table("timetable").select("*, rooms(room_number,room_name), subjects(code,name,credits), profiles(name)").order("day_order").order("start_time").execute().data or []
    # Defensive read-time de-duplication keeps the UI correct even before the
    # one-time database migration has removed legacy duplicate rows.
    seen=set(); clean=[]
    for row in rows:
        key=(row.get("day"),str(row.get("start_time"))[:5],str(row.get("end_time"))[:5],row.get("room_id"),row.get("section"),row.get("subject_id"),row.get("faculty_id"))
        if key in seen: continue
        seen.add(key); clean.append(row)
    return jsonify(clean)

@app.post("/api/timetable")
def add_timetable():
    profile = require("faculty")
    if not profile:
        return error("Sign in as faculty to create a timetable entry.", 401)
    data = request.get_json() or {}
    fields = ("day", "day_order", "start_time", "end_time", "room_id", "section", "subject_id")
    if not all(str(data.get(x, "")).strip() for x in fields):
        return error("Complete all timetable fields.")

    day = str(data["day"]).strip().title()
    day_order = int(data["day_order"]) if str(data["day_order"]).isdigit() else 0
    start_time, end_time = _time_value(data["start_time"]), _time_value(data["end_time"])
    start_minutes, end_minutes = _minutes(start_time), _minutes(end_time)
    if day not in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"} or not 1 <= day_order <= 6:
        return error("Choose a valid timetable day.")
    if start_minutes is None or end_minutes is None or start_minutes >= end_minutes:
        return error("Start time must be before end time.")

    db = client()
    subject = db.table("subjects").select("faculty_id").eq("id", data["subject_id"]).limit(1).execute().data
    if not subject:
        return error("Subject not found in the live syllabus catalog.", 404)
    lecturer_id = subject[0].get("faculty_id") or profile["id"]

    entries = db.table("timetable").select("id,day,start_time,end_time,room_id,section,faculty_id").eq("day", day).execute().data or []
    if any(_timetable_conflict(e, day, start_time, end_time, data["room_id"], str(data["section"]).strip(), lecturer_id) for e in entries):
        return error("Clash found for this room, lecturer or section.", 409)

    payload = {
        "day": day, "day_order": day_order, "start_time": start_time, "end_time": end_time,
        "room_id": data["room_id"], "section": str(data["section"]).strip(),
        "subject_id": data["subject_id"], "faculty_id": lecturer_id,
    }
    output = db.table("timetable").insert(payload).execute().data
    return jsonify(output[0]), 201

@app.patch("/api/timetable/<timetable_id>")
def update_timetable(timetable_id):
    profile = require("faculty")
    if not profile:
        return error("Sign in as faculty to edit timetable entries.", 401)
    db = client()
    existing = db.table("timetable").select("*").eq("id", timetable_id).limit(1).execute().data
    if not existing:
        return error("Timetable entry not found.", 404)
    current = existing[0]

    data = request.get_json() or {}
    fields = ("day", "day_order", "start_time", "end_time", "room_id", "section", "subject_id")
    if not all(str(data.get(x, "")).strip() for x in fields):
        return error("Complete all timetable fields.")
    day = str(data["day"]).strip().title()
    day_order = int(data["day_order"]) if str(data["day_order"]).isdigit() else 0
    start_time, end_time = _time_value(data["start_time"]), _time_value(data["end_time"])
    start_minutes, end_minutes = _minutes(start_time), _minutes(end_time)
    if day not in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"} or not 1 <= day_order <= 6:
        return error("Choose a valid timetable day.")
    if start_minutes is None or end_minutes is None or start_minutes >= end_minutes:
        return error("Start time must be before end time.")

    subject = db.table("subjects").select("faculty_id").eq("id", data["subject_id"]).limit(1).execute().data
    if not subject:
        return error("Subject not found in the live syllabus catalog.", 404)
    lecturer_id = subject[0].get("faculty_id") or profile["id"]

    entries = db.table("timetable").select("id,day,start_time,end_time,room_id,section,faculty_id").eq("day", day).execute().data or []
    section = str(data["section"]).strip()
    if any(_timetable_conflict(e, day, start_time, end_time, data["room_id"], section, lecturer_id, timetable_id) for e in entries):
        return error("Clash found for this room, lecturer or section.", 409)

    payload = {
        "day": day, "day_order": day_order, "start_time": start_time, "end_time": end_time,
        "room_id": data["room_id"], "section": section, "subject_id": data["subject_id"],
        "faculty_id": lecturer_id,
    }
    output = db.table("timetable").update(payload).eq("id", timetable_id).select("*").execute().data
    if not output: return error("The timetable update was not persisted. Refresh and try again.",500)
    return jsonify(output[0])

@app.delete("/api/timetable/<timetable_id>")
def delete_timetable(timetable_id):
    profile = require("faculty")
    if not profile: return error("Sign in as faculty to delete timetable entries.", 401)
    existing = client().table("timetable").select("id,faculty_id").eq("id", timetable_id).limit(1).execute().data
    if not existing: return error("Timetable entry not found.", 404)
    client().table("timetable").delete().eq("id", timetable_id).execute()
    return jsonify({"message":"Timetable entry deleted."})

@app.post("/api/timetable/upload")
def upload_timetable():
    profile = require("faculty")
    if not profile: return error("Sign in as faculty to upload a timetable.", 401)
    try:
        rows = _read_upload_rows(request.files.get("file"))
        if not rows: return error("The timetable file contains no data rows.")
        rooms = client().table("rooms").select("id,room_number").execute().data or []
        subjects = client().table("subjects").select("id,code,faculty_id").execute().data or []
        room_map = {str(r["room_number"]).strip().casefold(): r for r in rooms}
        subject_map = {str(s["code"]).strip().casefold(): s for s in subjects}
        day_order={"monday":1,"tuesday":2,"wednesday":3,"thursday":4,"friday":5,"saturday":6}
        normalized=[]; errors=[]
        for n,row in enumerate(rows, start=2):
            day=str(row.get("day","")).strip().title()
            room_no=str(row.get("room_number",row.get("room",""))).strip()
            code=str(row.get("subject_code",row.get("subject",""))).strip()
            section=str(row.get("section","")).strip()
            start=_time_value(row.get("start_time")); end=_time_value(row.get("end_time"))
            room=room_map.get(room_no.casefold()); subject=subject_map.get(code.casefold())
            if day.casefold() not in day_order: errors.append(f"Row {n}: invalid day '{day}'.")
            if not room: errors.append(f"Row {n}: room '{room_no}' was not found in SQL.")
            if not subject: errors.append(f"Row {n}: subject '{code}' was not found in SQL.")
            elif subject["faculty_id"] != profile["id"]: errors.append(f"Row {n}: subject '{code}' is not assigned to the signed-in faculty member.")
            if not section or not start or not end or start >= end: errors.append(f"Row {n}: section/time range is invalid.")
            normalized.append({"day":day,"day_order":day_order.get(day.casefold(),0),"start_time":start,"end_time":end,"room_id":room["id"] if room else None,"section":section,"subject_id":subject["id"] if subject else None,"faculty_id":profile["id"],"_row":n})
        if errors: return jsonify({"error":"Upload validation failed.","details":errors[:20]}),422

        # Treat an identical row as an idempotent re-upload rather than a clash.
        # This prevents the exact duplication visible in the timetable screenshot.
        existing = client().table("timetable").select("id,day,start_time,end_time,room_id,section,subject_id,faculty_id").execute().data or []
        key=lambda e:(e.get("day"),str(e.get("start_time"))[:5],str(e.get("end_time"))[:5],e.get("room_id"),e.get("section"),e.get("subject_id"),e.get("faculty_id"))
        existing_keys={key(e) for e in existing}
        staged=existing[:]; to_insert=[]; skipped=0
        for item in normalized:
            item_key=key(item)
            if item_key in existing_keys:
                skipped += 1
                continue
            clash=any(e.get("day")==item["day"] and str(e.get("start_time"))[:5] < item["end_time"] and str(e.get("end_time"))[:5] > item["start_time"] and (e.get("room_id")==item["room_id"] or e.get("section")==item["section"] or e.get("faculty_id")==profile["id"]) for e in staged)
            if clash: return jsonify({"error":f"Upload clash on row {item['_row']}: room, section or lecturer already has an overlapping booking."}),409
            staged.append(item); existing_keys.add(item_key); to_insert.append({k:v for k,v in item.items() if not k.startswith("_")})
        saved=client().table("timetable").insert(to_insert).execute().data if to_insert else []
        return jsonify({"inserted":len(saved),"skipped":skipped,"rows":saved}),201
    except ValueError as exc: return error(str(exc),422)
    except Exception as exc: return error(f"Timetable upload failed: {exc}",500)

@app.get("/api/progress")
def progress():
    profile = require("faculty")
    if not profile: return error("You do not have access to syllabus progress.", 403)
    rows = client().table("syllabus_progress").select("*, subjects(code,name,credits,semester,faculty_id), profiles(name)").order("updated_at",desc=True).execute().data or []
    return jsonify(rows)

@app.post("/api/progress")
def add_progress():
    profile=require("faculty")
    if not profile:return error("Sign in as faculty to update syllabus coverage.",401)
    data=request.get_json() or {}; subject=client().table("subjects").select("faculty_id").eq("id",data.get("subject_id")).execute().data
    if not subject:return error("Subject not found in the live syllabus catalog.",404)
    try: coverage=float(data["coverage_percent"]); week=int(data["week_number"])
    except (KeyError,ValueError,TypeError):return error("Coverage and week must be valid numbers.")
    if not 0<=coverage<=100 or not 1<=week<=30 or not str(data.get("topics_covered","")).strip():return error("Complete week, coverage and topics.")
    record={"subject_id":data["subject_id"],"week_number":week,"coverage_percent":coverage,"topics_covered":data["topics_covered"].strip(),"updated_by":profile["id"],"updated_at":now()}
    output=client().table("syllabus_progress").upsert(record,on_conflict="subject_id,week_number").execute().data[0]
    return jsonify(output),201

@app.patch("/api/progress/<progress_id>")
def update_progress(progress_id):
    profile=require("faculty")
    if not profile:return error("Sign in as faculty to edit syllabus progress.",401)
    existing=client().table("syllabus_progress").select("*").eq("id",progress_id).limit(1).execute().data
    if not existing:return error("Syllabus progress entry not found.",404)
    current=existing[0]
    data=request.get_json() or {}
    subject_id=str(data.get("subject_id",current["subject_id"])).strip()
    try: coverage=float(data.get("coverage_percent",current["coverage_percent"])); week=int(data.get("week_number",current["week_number"]))
    except (ValueError,TypeError): return error("Coverage and week must be valid numbers.")
    topics=str(data.get("topics_covered",current["topics_covered"])).strip()
    subject=client().table("subjects").select("faculty_id").eq("id",subject_id).execute().data
    if not subject: return error("Subject not found in the live syllabus catalog.",404)
    if not 0<=coverage<=100 or not 1<=week<=30 or not topics:return error("Complete week, coverage and topics.")
    duplicate=client().table("syllabus_progress").select("id").eq("subject_id",subject_id).eq("week_number",week).neq("id",progress_id).limit(1).execute().data
    if duplicate:return error("Another syllabus entry already exists for this subject and week.",409)
    record={"subject_id":subject_id,"week_number":week,"coverage_percent":coverage,"topics_covered":topics,"updated_by":profile["id"],"updated_at":now()}
    output=client().table("syllabus_progress").update(record).eq("id",progress_id).select("*").execute().data
    if not output: return error("The syllabus update was not persisted. Refresh and try again.",500)
    return jsonify(output[0])

@app.delete("/api/progress/<progress_id>")
def delete_progress(progress_id):
    profile=require("faculty")
    if not profile:return error("Sign in as faculty to delete syllabus progress.",401)
    db=client()
    existing=db.table("syllabus_progress").select("id,subject_id").eq("id",progress_id).limit(1).execute().data
    if not existing:return error("Syllabus progress entry not found.",404)
    db.table("syllabus_progress").delete().eq("id",progress_id).execute()
    return jsonify({"message":"Syllabus progress deleted."})

@app.post("/api/progress/upload")
def upload_progress():
    profile=require("faculty")
    if not profile: return error("Sign in as faculty to upload syllabus progress.",401)
    try:
        rows=_read_upload_rows(request.files.get("file"))
        if not rows:return error("The syllabus progress file contains no data rows.")
        subjects=client().table("subjects").select("id,code,faculty_id").execute().data
        subject_map={s["code"].strip().casefold():s for s in subjects}
        payload=[];errors=[]
        for n,row in enumerate(rows,start=2):
            code=str(row.get("subject_code",row.get("code",""))).strip(); week_raw=row.get("week_number",row.get("week","")); cov_raw=row.get("coverage_percent",row.get("coverage","")); topics=str(row.get("topics_covered",row.get("topics",""))).strip(); subject=subject_map.get(code.casefold())
            try: week=int(float(week_raw)); coverage=float(cov_raw)
            except (TypeError,ValueError): errors.append(f"Row {n}: week and coverage must be numeric."); continue
            if not subject: errors.append(f"Row {n}: subject '{code}' was not found in SQL.")
            elif subject.get("faculty_id") and subject["faculty_id"] != profile["id"]: errors.append(f"Row {n}: subject '{code}' is not assigned to the signed-in faculty member.")
            if not 1<=week<=30: errors.append(f"Row {n}: week must be between 1 and 30.")
            if not 0<=coverage<=100: errors.append(f"Row {n}: coverage must be between 0 and 100.")
            if not topics: errors.append(f"Row {n}: topics_covered is required.")
            payload.append({"subject_id":subject["id"] if subject else None,"week_number":week,"coverage_percent":coverage,"topics_covered":topics,"updated_by":profile["id"],"updated_at":now(),"_row":n})
        if errors:return jsonify({"error":"Upload validation failed.","details":errors[:20]}),422
        dedup={}
        for item in payload: dedup[(item["subject_id"], item["week_number"])] = item
        clean=[{k:v for k,v in x.items() if not k.startswith("_")} for x in dedup.values()]
        saved=client().table("syllabus_progress").upsert(clean,on_conflict="subject_id,week_number").execute().data or []
        return jsonify({"upserted":len(saved),"rows":saved,"received":len(rows)}),201
    except ValueError as exc:return error(str(exc),422)
    except Exception as exc:return error(f"Syllabus progress upload failed: {exc}",500)

if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.getenv("PORT","5000")), debug=False)
