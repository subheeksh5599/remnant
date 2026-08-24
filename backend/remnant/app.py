"""
REMNANT — FastAPI application.

Serves the REMNANT core: remnants, expressions, hypotheses, experiments, belief
updates, and the persistent Mind state. The deterministic reasoning (grouping,
hypothesis accounting, experiment planning) runs here; the Minds agent anchors
long-term continuity.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .experiments import apply_observed_outcome, plan_experiment
from .inference import assess_hypotheses
from .belief import current_belief
from .minds import MindsClient
from .models import (AudienceExpression, CreatorDecision, Remnant, Source)
from .store import Store


def _parse_dt(s: Optional[str]) -> datetime:
    if s is None:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


_VALID_DECISIONS = {"adopted", "rejected", "deferred", "no_response"}

app = FastAPI(title="REMNANT", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = Store(os.getenv("STORAGE_PATH", "./data/remnant.db"))
minds = MindsClient()


# --- request/response models -------------------------------------------------

class IngestExpressionRequest(BaseModel):
    text: str
    source_kind: str
    source_id: str
    occurred_at: Optional[str] = None
    url: Optional[str] = None
    audience_segment: Optional[str] = None


class CreateRemnantRequest(BaseModel):
    title: str
    underlying_need_hypothesis: str


class CreatorDecisionRequest(BaseModel):
    decision: str
    reason: Optional[str] = None


class ExperimentOutcomeRequest(BaseModel):
    observed_value: float


# --- endpoints ---------------------------------------------------------------

@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "mind": minds.state().ok, "remnants": len(store.all())}


@app.get("/api/remnants")
def list_remnants() -> list[dict]:
    return [r.model_dump(mode="json") for r in store.all()]


@app.post("/api/remnants")
def create_remnant(req: CreateRemnantRequest) -> dict:
    r = Remnant(title=req.title, underlying_need_hypothesis=req.underlying_need_hypothesis)
    store.upsert(r)
    return r.model_dump(mode="json")


@app.get("/api/remnants/{rid}")
def get_remnant(rid: str) -> dict:
    r = store.get(rid)
    if r is None:
        raise HTTPException(status_code=404, detail="remnant not found")
    return r.model_dump(mode="json")


@app.post("/api/remnants/{rid}/expressions")
def add_expression(rid: str, req: IngestExpressionRequest) -> dict:
    r = store.get(rid)
    if r is None:
        raise HTTPException(status_code=404, detail="remnant not found")
    expr = AudienceExpression(
        text=req.text,
        source=Source(
            kind=req.source_kind,
            source_id=req.source_id,
            url=req.url,
        ),
        occurred_at=_parse_dt(req.occurred_at),
        audience_segment=req.audience_segment,
    )
    r.expressions.append(expr)
    # Re-run hypothesis accounting with the new evidence.
    r.assessments = assess_hypotheses(r)
    r.history.append(f"expression {expr.expression_id} ingested: {req.text[:60]}")
    store.upsert(r)
    return r.model_dump(mode="json")


@app.post("/api/remnants/{rid}/decisions")
def add_decision(rid: str, req: CreatorDecisionRequest) -> dict:
    r = store.get(rid)
    if r is None:
        raise HTTPException(status_code=404, detail="remnant not found")
    if req.decision not in _VALID_DECISIONS:
        raise HTTPException(status_code=422, detail=f"decision must be one of {sorted(_VALID_DECISIONS)}")
    r.creator_decisions.append(
        CreatorDecision(decision=req.decision, reason=req.reason)
    )
    r.history.append(f"creator decision: {req.decision} ({req.reason or 'no reason'})")
    store.upsert(r)
    return r.model_dump(mode="json")


@app.post("/api/remnants/{rid}/experiments")
def create_experiment(rid: str) -> dict:
    r = store.get(rid)
    if r is None:
        raise HTTPException(status_code=404, detail="remnant not found")
    exp = plan_experiment(r)
    r.experiments.append(exp)
    r.history.append(f"experiment planned: {exp.experiment_id}")
    store.upsert(r)
    return exp.model_dump(mode="json")


@app.post("/api/remnants/{rid}/experiments/{eid}/outcome")
def record_outcome(rid: str, eid: str, req: ExperimentOutcomeRequest) -> dict:
    r = store.get(rid)
    if r is None:
        raise HTTPException(status_code=404, detail="remnant not found")
    exp = next((e for e in r.experiments if e.experiment_id == eid), None)
    if exp is None:
        raise HTTPException(status_code=404, detail="experiment not found")
    apply_observed_outcome(r, exp, observed_value=req.observed_value)
    store.upsert(r)
    return r.model_dump(mode="json")


@app.get("/api/remnants/{rid}/belief")
def remnant_belief(rid: str) -> dict:
    """Answer 'what do you currently believe about this need?' — the full chain."""
    r = store.get(rid)
    if r is None:
        raise HTTPException(status_code=404, detail="remnant not found")
    return {"remnant_id": rid, "belief": current_belief(r)}


@app.get("/api/mind")
def mind_state() -> dict:
    st = minds.state()
    return {
        "ok": st.ok,
        "mind_id": st.mind_id,
        "name": st.name,
        "enabled": st.enabled,
        "cognition_balance": st.cognition_balance,
        "available": minds.available(),
        "error": st.error,
    }