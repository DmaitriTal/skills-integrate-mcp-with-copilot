"""
High School Management System API

A simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School. This version uses
SQLite via SQLModel for persistence (activities + signups).
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

from sqlmodel import Session, select
from models import Activity, Signup, create_db_and_tables, engine


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


@app.on_event("startup")
def on_startup():
    # Ensure database and tables exist
    create_db_and_tables()
    # Seed initial activities if none exist
    with Session(engine) as session:
        any_activity = session.exec(select(Activity)).first()
        if not any_activity:
            seed = [
                Activity(name="Chess Club", description="Learn strategies and compete in chess tournaments", schedule="Fridays, 3:30 PM - 5:00 PM", max_participants=12),
                Activity(name="Programming Class", description="Learn programming fundamentals and build software projects", schedule="Tuesdays and Thursdays, 3:30 PM - 4:30 PM", max_participants=20),
                Activity(name="Gym Class", description="Physical education and sports activities", schedule="Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", max_participants=30),
                Activity(name="Soccer Team", description="Join the school soccer team and compete in matches", schedule="Tuesdays and Thursdays, 4:00 PM - 5:30 PM", max_participants=22),
                Activity(name="Basketball Team", description="Practice and play basketball with the school team", schedule="Wednesdays and Fridays, 3:30 PM - 5:00 PM", max_participants=15),
                Activity(name="Art Club", description="Explore your creativity through painting and drawing", schedule="Thursdays, 3:30 PM - 5:00 PM", max_participants=15),
                Activity(name="Drama Club", description="Act, direct, and produce plays and performances", schedule="Mondays and Wednesdays, 4:00 PM - 5:30 PM", max_participants=20),
                Activity(name="Math Club", description="Solve challenging problems and participate in math competitions", schedule="Tuesdays, 3:30 PM - 4:30 PM", max_participants=10),
                Activity(name="Debate Team", description="Develop public speaking and argumentation skills", schedule="Fridays, 4:00 PM - 5:30 PM", max_participants=12),
            ]
            session.add_all(seed)
            session.commit()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    results = {}
    with Session(engine) as session:
        activities = session.exec(select(Activity)).all()
        for a in activities:
            signups = session.exec(select(Signup).where(Signup.activity_id == a.id)).all()
            participants = [s.email for s in signups]
            results[a.name] = {
                "description": a.description,
                "schedule": a.schedule,
                "max_participants": a.max_participants,
                "participants": participants,
            }
    return results


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity (persisted)"""
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Check if already signed up
        existing = session.exec(select(Signup).where(Signup.activity_id == activity.id).where(Signup.email == email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        # Check capacity
        count = session.exec(select(Signup).where(Signup.activity_id == activity.id)).count()
        if count >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        signup = Signup(activity_id=activity.id, email=email)
        session.add(signup)
        session.commit()
        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity (persisted)"""
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        signup = session.exec(select(Signup).where(Signup.activity_id == activity.id).where(Signup.email == email)).first()
        if not signup:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        session.delete(signup)
        session.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}
