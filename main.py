from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import sqlite3
import uuid
import hashlib
import secrets
from datetime import datetime, date, timedelta
import json
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

app = FastAPI(title="Tennis Match LA", description="LA Tennis Player Matching System")

# Configuration
DATABASE_URL = "sqlite:///./tennis_match.db"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@tennis-match-la.com")

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Security
security = HTTPBearer()

# Scheduler for daily tasks
scheduler = AsyncIOScheduler()

# Database Models
class Player(BaseModel):
    name: str
    email: EmailStr
    skill_level: float
    preferred_days: List[str]
    preferred_times: List[str]
    location_zip: str
    travel_radius: int = 15
    match_types: List[str]
    competitive_level: str = "casual"

class PlayerLogin(BaseModel):
    email: EmailStr
    password: str

class MatchFeedback(BaseModel):
    skill_accuracy: int  # 1-5
    enjoyment: int  # 1-5
    would_play_again: bool

# Database initialization
def init_db():
    conn = sqlite3.connect("tennis_match.db")
    cursor = conn.cursor()

    # Players table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            skill_level REAL NOT NULL,
            skill_trend TEXT DEFAULT 'stable',
            reliability_score REAL DEFAULT 1.0,
            preferred_days TEXT,
            preferred_times TEXT,
            location_zip TEXT,
            travel_radius INTEGER DEFAULT 15,
            match_types TEXT,
            total_matches INTEGER DEFAULT 0,
            feedback_score REAL DEFAULT 0.0,
            competitive_level TEXT DEFAULT 'casual',
            min_skill_gap REAL DEFAULT 0.0,
            max_skill_gap REAL DEFAULT 1.0,
            preferred_opponent_skill TEXT DEFAULT 'similar',
            avoid_players TEXT,
            is_active BOOLEAN DEFAULT 1,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Matches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id TEXT PRIMARY KEY,
            player1_id TEXT NOT NULL,
            player2_id TEXT NOT NULL,
            match_type TEXT NOT NULL,
            suggested_location TEXT,
            match_date DATE NOT NULL,
            status TEXT DEFAULT 'pending',
            scores TEXT,
            player1_feedback TEXT,
            player2_feedback TEXT,
            match_quality_score REAL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player1_id) REFERENCES players (id),
            FOREIGN KEY (player2_id) REFERENCES players (id)
        )
    """)

    # Admin users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add admin user
    admin_id = str(uuid.uuid4())
    cursor.execute("INSERT OR IGNORE INTO admin_users (id, email) VALUES (?, ?)",
                   (admin_id, ADMIN_EMAIL))

    conn.commit()
    conn.close()

# Database helper functions
def get_db():
    conn = sqlite3.connect("tennis_match.db")
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_player_token(player_id: str) -> str:
    return secrets.token_urlsafe(32)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE id = ?", (token,))
    player = cursor.fetchone()
    conn.close()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return dict(player)

# Sample data for testing
def create_sample_data():
    conn = get_db()
    cursor = conn.cursor()

    # Check if we already have players
    cursor.execute("SELECT COUNT(*) as count FROM players")
    count = cursor.fetchone()["count"]

    if count == 0:
        sample_players = [
            ("John Doe", "john@tennis.com", 3.5, ["monday", "wednesday"], ["evening"], "90210", ["singles"]),
            ("Jane Smith", "jane@tennis.com", 4.0, ["tuesday", "thursday"], ["morning"], "90401", ["singles", "doubles"]),
            ("Mike Johnson", "mike@tennis.com", 3.0, ["saturday", "sunday"], ["afternoon"], "90025", ["singles"]),
            ("Sarah Wilson", "sarah@tennis.com", 4.5, ["monday", "friday"], ["evening"], "90265", ["singles", "doubles"]),
            ("Tom Brown", "tom@tennis.com", 3.5, ["tuesday", "saturday"], ["morning"], "90049", ["doubles"]),
        ]

        for name, email, skill, days, times, zip_code, match_types in sample_players:
            player_id = str(uuid.uuid4())
            password_hash = hash_password("password123")  # Default password for testing

            cursor.execute("""
                INSERT INTO players (
                    id, name, email, password_hash, skill_level,
                    preferred_days, preferred_times, location_zip,
                    match_types, created, last_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_id, name, email, password_hash, skill,
                json.dumps(days), json.dumps(times), zip_code,
                json.dumps(match_types), datetime.now(), datetime.now()
            ))

    conn.commit()
    conn.close()

# Matching algorithm
def calculate_distance(zip1: str, zip2: str) -> float:
    # Simple distance calculation (would use real distance API in production)
    return abs(int(zip1[:3]) - int(zip2[:3])) * 5  # Rough estimate in miles

def has_common_time(times1: List[str], times2: List[str]) -> bool:
    return bool(set(times1) & set(times2))

def has_common_day(days1: List[str], days2: List[str]) -> bool:
    return bool(set(days1) & set(days2))

def generate_matches():
    conn = get_db()
    cursor = conn.cursor()

    # Get all active players
    cursor.execute("SELECT * FROM players WHERE is_active = 1")
    players = [dict(row) for row in cursor.fetchall()]

    matches_created = []

    for i, player1 in enumerate(players):
        for player2 in players[i+1:]:
            # Skip if they've played recently
            cursor.execute("""
                SELECT id FROM matches
                WHERE ((player1_id = ? AND player2_id = ?) OR (player1_id = ? AND player2_id = ?))
                AND match_date >= date('now', '-14 days')
                AND status != 'cancelled'
            """, (player1["id"], player2["id"], player2["id"], player1["id"]))

            if cursor.fetchone():
                continue

            # Skill compatibility
            skill_gap = abs(player1["skill_level"] - player2["skill_level"])
            if skill_gap > 1.0:
                continue

            # Location compatibility
            distance = calculate_distance(player1["location_zip"], player2["location_zip"])
            if distance > min(player1["travel_radius"], player2["travel_radius"]):
                continue

            # Time compatibility
            days1 = json.loads(player1["preferred_days"])
            days2 = json.loads(player2["preferred_days"])
            times1 = json.loads(player1["preferred_times"])
            times2 = json.loads(player2["preferred_times"])

            if not (has_common_day(days1, days2) and has_common_time(times1, times2)):
                continue

            # Create match
            match_id = str(uuid.uuid4())
            match_date = (datetime.now() + timedelta(days=1)).date()

            cursor.execute("""
                INSERT INTO matches (
                    id, player1_id, player2_id, match_type,
                    match_date, status, suggested_location
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, player1["id"], player2["id"], "singles",
                match_date, "pending", f"Central LA Courts ({distance:.0f} miles from both)"
            ))

            matches_created.append({
                "id": match_id,
                "player1": player1["name"],
                "player2": player2["name"],
                "date": match_date,
                "distance": distance
            })

    conn.commit()
    conn.close()
    return matches_created

# API Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    password_hash = hash_password(password)

    cursor.execute("""
        SELECT * FROM players
        WHERE email = ? AND password_hash = ? AND is_active = 1
    """, (email, password_hash))

    player = cursor.fetchone()
    conn.close()

    if not player:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password"
        })

    # Update last active
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET last_active = ? WHERE id = ?",
                   (datetime.now(), player["id"]))
    conn.commit()
    conn.close()

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="player_token", value=player["id"])
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = request.cookies.get("player_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE id = ?", (token,))
    player = cursor.fetchone()

    if not player:
        return RedirectResponse(url="/", status_code=303)

    # Get upcoming matches
    cursor.execute("""
        SELECT m.*, p.name as opponent_name, p.skill_level as opponent_skill
        FROM matches m
        JOIN players p ON (m.player1_id = ? AND m.player2_id = p.id) OR
                         (m.player2_id = ? AND m.player1_id = p.id)
        WHERE m.match_date >= date('now') AND m.status = 'pending'
        ORDER BY m.match_date
        LIMIT 5
    """, (player["id"], player["id"]))

    upcoming_matches = [dict(row) for row in cursor.fetchall()]

    # Get recent matches
    cursor.execute("""
        SELECT m.*, p.name as opponent_name, m.match_quality_score
        FROM matches m
        JOIN players p ON (m.player1_id = ? AND m.player2_id = p.id) OR
                         (m.player2_id = ? AND m.player1_id = p.id)
        WHERE m.status = 'completed'
        ORDER BY m.match_date DESC
        LIMIT 5
    """, (player["id"], player["id"]))

    recent_matches = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "player": dict(player),
        "upcoming_matches": upcoming_matches,
        "recent_matches": recent_matches
    })

@app.get("/preferences", response_class=HTMLResponse)
async def preferences(request: Request):
    token = request.cookies.get("player_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE id = ?", (token,))
    player = cursor.fetchone()
    conn.close()

    if not player:
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse("preferences.html", {
        "request": request,
        "player": dict(player)
    })

@app.post("/preferences")
async def update_preferences(
    request: Request,
    skill_level: float = Form(...),
    preferred_days: str = Form(...),
    preferred_times: str = Form(...),
    location_zip: str = Form(...),
    travel_radius: int = Form(...),
    match_types: str = Form(...)
):
    token = request.cookies.get("player_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)

    days = [day.strip() for day in preferred_days.split(",") if day.strip()]
    times = [time.strip() for time in preferred_times.split(",") if time.strip()]
    types_ = [type_.strip() for type_ in match_types.split(",") if type_.strip()]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE players SET
            skill_level = ?,
            preferred_days = ?,
            preferred_times = ?,
            location_zip = ?,
            travel_radius = ?,
            match_types = ?,
            last_active = ?
        WHERE id = ?
    """, (
        skill_level, json.dumps(days), json.dumps(times),
        location_zip, travel_radius, json.dumps(types_),
        datetime.now(), token
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/match/{match_id}/confirm")
async def confirm_match(match_id: str, confirmed: bool = Form(...)):
    # Implementation for match confirmation
    return {"status": "success"}

@app.post("/match/{match_id}/feedback")
async def submit_feedback(match_id: str, feedback: MatchFeedback):
    # Implementation for match feedback
    return {"status": "success"}

@app.get("/health")
async def health_check():
    conn = get_db()
    cursor = conn.cursor()

    # Basic health checks
    cursor.execute("SELECT COUNT(*) as count FROM players WHERE is_active = 1")
    player_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM matches WHERE status = 'pending' AND match_date >= date('now')")
    pending_matches = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM system_logs WHERE created >= datetime('now', '-1 day') AND log_level = 'error'")
    errors_24h = cursor.fetchone()["count"]

    conn.close()

    return {
        "status": "healthy",
        "total_players": player_count,
        "pending_matches": pending_matches,
        "errors_24h": errors_24h,
        "timestamp": datetime.now().isoformat()
    }

# Admin routes
@app.get("/admin/trigger_matching")
async def trigger_matching():
    matches = generate_matches()
    return {"status": "success", "matches_created": len(matches), "matches": matches}

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM players WHERE is_active = 1")
    total_players = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM matches WHERE status = 'pending' AND match_date >= date('now')")
    pending_matches = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM matches WHERE status = 'completed'")
    completed_matches = cursor.fetchone()["count"]

    # Recent matches
    cursor.execute("""
        SELECT m.*, p1.name as player1_name, p2.name as player2_name
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        ORDER BY m.created DESC
        LIMIT 10
    """)

    recent_matches = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "total_players": total_players,
        "pending_matches": pending_matches,
        "completed_matches": completed_matches,
        "recent_matches": recent_matches
    })

# Startup
@app.on_event("startup")
async def startup_event():
    init_db()
    create_sample_data()

    # Schedule daily matching at 2 AM
    scheduler.add_job(
        generate_matches,
        'cron',
        hour=2,
        minute=0,
        id='daily_matching'
    )
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)