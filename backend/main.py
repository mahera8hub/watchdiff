import json, os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from dotenv import load_dotenv

from database import create_db, get_session
from models import Endpoint, DiffRecord
from schemas import EndpointCreate, EndpointRead, DiffRead
from scheduler import scheduler, register_job, remove_job, poll_endpoint

load_dotenv()
app = FastAPI(title="watchdiff API", version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "*")],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    create_db()
    scheduler.start()
    # Re-register all active endpoints after restart
    from database import engine
    from sqlmodel import Session
    with Session(engine) as session:
        eps = session.exec(select(Endpoint).where(Endpoint.is_active == True)).all()
        for ep in eps:
            register_job(ep.id, ep.interval_minutes)

@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()

@app.get("/health")
def health(): return {"status": "ok"}

# ── Endpoints CRUD ───────────────────────────────────────────

@app.post("/endpoints", response_model=EndpointRead)
def create_endpoint(data: EndpointCreate, session: Session = Depends(get_session)):
    ep = Endpoint(
        url=data.url, method=data.method,
        headers=json.dumps(data.headers) if data.headers else None,
        body=json.dumps(data.body) if data.body else None,
        interval_minutes=data.interval_minutes,
        tags=data.tags,
        ignore_array_order=data.ignore_array_order,
    )
    session.add(ep)
    session.commit()
    session.refresh(ep)
    register_job(ep.id, ep.interval_minutes)
    return ep

@app.get("/endpoints", response_model=list[EndpointRead])
def list_endpoints(session: Session = Depends(get_session)):
    return session.exec(select(Endpoint)).all()

@app.get("/endpoints/{endpoint_id}", response_model=EndpointRead)
def get_endpoint(endpoint_id: int, session: Session = Depends(get_session)):
    ep = session.get(Endpoint, endpoint_id)
    if not ep: raise HTTPException(status_code=404, detail="Not found")
    return ep

@app.delete("/endpoints/{endpoint_id}")
def delete_endpoint(endpoint_id: int, session: Session = Depends(get_session)):
    ep = session.get(Endpoint, endpoint_id)
    if not ep: raise HTTPException(status_code=404, detail="Not found")
    remove_job(endpoint_id)
    session.delete(ep)
    session.commit()
    return {"ok": True}

@app.post("/endpoints/{endpoint_id}/check")
def manual_check(endpoint_id: int):
    poll_endpoint(endpoint_id)
    return {"ok": True}

# ── Diffs ────────────────────────────────────────────────────

@app.get("/endpoints/{endpoint_id}/diffs", response_model=list[DiffRead])
def get_diffs(endpoint_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(DiffRecord)
        .where(DiffRecord.endpoint_id == endpoint_id)
        .order_by(DiffRecord.created_at.desc())
    ).all()

@app.get("/endpoints/{endpoint_id}/diffs/latest", response_model=DiffRead | None)
def get_latest_diff(endpoint_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(DiffRecord)
        .where(DiffRecord.endpoint_id == endpoint_id)
        .order_by(DiffRecord.created_at.desc())
    ).first()
