import json, time
from datetime import datetime
import httpx
from sqlmodel import Session, select
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import engine
from models import Endpoint, Snapshot, DiffRecord
from differ import hash_response, semantic_diff, classify_severity

scheduler = BackgroundScheduler()

def poll_endpoint(endpoint_id: int):
    with Session(engine) as session:
        ep = session.get(Endpoint, endpoint_id)
        if not ep or not ep.is_active:
            return

        headers = json.loads(ep.headers) if ep.headers else {}
        start = time.time()

        try:
            resp = httpx.request(
                ep.method, ep.url, headers=headers,
                timeout=10.0
            )
            elapsed = int((time.time() - start) * 1000)
            try:
                body = resp.json()
            except Exception:
                body = {"_raw": resp.text}

            new_hash = hash_response(body)

            # get previous snapshot
            prev = session.exec(
                select(Snapshot)
                .where(Snapshot.endpoint_id == endpoint_id)
                .order_by(Snapshot.captured_at.desc())
            ).first()

            # save new snapshot
            snap = Snapshot(
                endpoint_id=endpoint_id,
                response_body=json.dumps(body),
                status_code=resp.status_code,
                response_time_ms=elapsed,
                content_hash=new_hash,
            )
            session.add(snap)
            session.flush()  # get snap.id before commit

            if prev and prev.content_hash != new_hash:
                old_body = json.loads(prev.response_body or "{}"),
                diff = semantic_diff(
                    old_body[0], body,
                    ignore_order=ep.ignore_array_order
                )
                severity = classify_severity(diff)
                rec = DiffRecord(
                    endpoint_id=endpoint_id,
                    snapshot_before_id=prev.id,
                    snapshot_after_id=snap.id,
                    diff_json=json.dumps(diff, default=str),
                    severity=severity,
                )
                session.add(rec)
                ep.last_status = "CHANGED"
            else:
                ep.last_status = "OK"

            ep.last_checked_at = datetime.utcnow()
            ep.last_status_code = resp.status_code
            session.commit()

        except Exception as e:
            ep.last_status = "ERROR"
            ep.last_checked_at = datetime.utcnow()
            session.commit()

def register_job(endpoint_id: int, interval_minutes: int):
    job_id = f"poll_{endpoint_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        poll_endpoint,
        trigger=IntervalTrigger(minutes=interval_minutes),
        args=[endpoint_id],
        id=job_id,
    )

def remove_job(endpoint_id: int):
    job_id = f"poll_{endpoint_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
