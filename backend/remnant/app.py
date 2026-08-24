"""
REMNANT — FastAPI application.

Wires the layers:
  - config (centralized, validated at startup)
  - structured logging + request-id middleware (correlation)
  - deterministic core (inference, experiments, belief) — no LLM inside the math
  - Minds client (persistent agent; explicit failure, never silent fallback)
  - autonomous observatory (background loop; proactive follow-up)
  - store (atomic persistence)

API versioning: all routes are under /api/v1.
Error schema: {"error": {"code", "message", "request_id"}}.
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .belief import current_belief
from .config import settings
from .experiments import apply_observed_outcome, plan_experiment
from .inference import assess_hypotheses
from .logging_config import RequestIdMiddleware, audit, log
from .minds import MindsClient
from .models import (AudienceExpression, CreatorDecision, Remnant, Source)
from .observatory import Observatory
from .store import Store

store = Store(settings.storage_path)
minds_client = MindsClient()
observatory: Observatory | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global observatory
    observatory = Observatory(store)
    observatory.start()
    yield
    if observatory:
        observatory.stop()


app = FastAPI(
    title="REMNANT",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)


def _err(request: Request, code: str, message: str, status: int) -> HTTPException:
    # request_id must NEVER be None in the error schema. If the request-id
    # middleware hasn't run yet (auth failures fire before it), generate one.
    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
    return HTTPException(
        status_code=status,
        detail={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
    )


# CORS from config (never "*" in production unless explicitly set)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestIdMiddleware)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Baseline security headers for any deployment."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


# --- auth gate (only when REMNANT_REQUIRE_AUTH=true) ---------------------------

async def _auth(request: Request) -> None:
    if not settings.require_auth:
        return
    token = request.headers.get("Authorization", "")
    expected = f"Bearer {settings.api_token or ''}"
    if token != expected:
        raise _err(request, "unauthorized", "missing or invalid token", 401)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    try:
        await _auth(request)
    except HTTPException as e:
        return e if hasattr(e, "body") else __import__("fastapi.responses", fromlist=["JSONResponse"]).JSONResponse(
            status_code=e.status_code,
            content=e.detail,
        )
    return await call_next(request)


# --- request/response models ---------------------------------------------------

class IngestExpressionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    source_kind: str = Field(min_length=1, max_length=64)
    source_id: str = Field(min_length=1, max_length=128)
    occurred_at: Optional[str] = None
    url: Optional[str] = None
    audience_segment: Optional[str] = None


class CreateRemnantRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    underlying_need_hypothesis: str = Field(min_length=1, max_length=1000)


class CreatorDecisionRequest(BaseModel):
    decision: str
    reason: Optional[str] = None


class ExperimentOutcomeRequest(BaseModel):
    observed_value: float


# --- lifespan helpers -------------------------------------------------------------

def _parse_dt(s: Optional[str]) -> datetime:
    if s is None:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


_VALID_DECISIONS = {"adopted", "rejected", "deferred", "no_response"}


# --- endpoints (v1) ---------------------------------------------------------------

@app.get("/api/v1/health")
def health() -> dict:
    mind_ok = minds_client.state()
    return {
        "ok": True,
        "mind": mind_ok.ok,
        "remnants": len(store.all()),
        "env": {
            "mind_configured": settings.minds_configured,
        },
    }


@app.get("/api/v1/readyz")
def readyz() -> dict:
    """Readiness: the app is ready to serve when the store is writable."""
    try:
        probe = store.all()
        return {"ok": True, "remnants": len(probe)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail={"error": {"code": "not_ready", "message": str(e)}})


@app.get("/api/v1/livez")
def livez() -> dict:
    """Liveness: the process is up."""
    return {"ok": True}


@app.get("/api/v1/remnants")
def list_remnants(request: Request) -> list[dict]:
    return [r.model_dump(mode="json") for r in store.all()]


@app.post("/api/v1/remnants")
def create_remnant(req: CreateRemnantRequest, request: Request) -> dict:
    r = Remnant(title=req.title, underlying_need_hypothesis=req.underlying_need_hypothesis)
    store.upsert(r)
    audit("remnant.created", request_id=getattr(request.state, "request_id", None), remnant_id=r.remnant_id)
    return r.model_dump(mode="json")


@app.get("/api/v1/remnants/{rid}")
def get_remnant(rid: str, request: Request) -> dict:
    r = store.get(rid)
    if r is None:
        raise _err(request, "not_found", "remnant not found", 404)
    return r.model_dump(mode="json")


@app.post("/api/v1/remnants/{rid}/expressions")
def add_expression(rid: str, req: IngestExpressionRequest, request: Request) -> dict:
    r = store.get(rid)
    if r is None:
        raise _err(request, "not_found", "remnant not found", 404)
    expr = AudienceExpression(
        text=req.text,
        source=Source(kind=req.source_kind, source_id=req.source_id, url=req.url),
        occurred_at=_parse_dt(req.occurred_at),
        audience_segment=req.audience_segment,
    )
    r.expressions.append(expr)
    r.assessments = assess_hypotheses(r)
    r.touch()
    r.history.append(f"expression {expr.expression_id} ingested: {req.text[:60]}")
    store.upsert(r)
    audit("expression.ingested", request_id=getattr(request.state, "request_id", None), remnant_id=rid)
    return r.model_dump(mode="json")


@app.post("/api/v1/remnants/{rid}/decisions")
def add_decision(rid: str, req: CreatorDecisionRequest, request: Request) -> dict:
    r = store.get(rid)
    if r is None:
        raise _err(request, "not_found", "remnant not found", 404)
    if req.decision not in _VALID_DECISIONS:
        raise _err(request, "invalid_decision", f"decision must be one of {sorted(_VALID_DECISIONS)}", 422)
    r.creator_decisions.append(CreatorDecision(decision=req.decision, reason=req.reason))
    r.touch()
    r.history.append(f"creator decision: {req.decision} ({req.reason or 'no reason'})")
    store.upsert(r)
    audit("decision.recorded", request_id=getattr(request.state, "request_id", None), remnant_id=rid, decision=req.decision)
    return r.model_dump(mode="json")


@app.post("/api/v1/remnants/{rid}/experiments")
def create_experiment(rid: str, request: Request) -> dict:
    r = store.get(rid)
    if r is None:
        raise _err(request, "not_found", "remnant not found", 404)
    exp = plan_experiment(r)
    r.experiments.append(exp)
    r.touch()
    r.history.append(f"experiment planned: {exp.experiment_id}")
    store.upsert(r)
    audit("experiment.planned", request_id=getattr(request.state, "request_id", None), remnant_id=rid, experiment_id=exp.experiment_id)
    return exp.model_dump(mode="json")


@app.post("/api/v1/remnants/{rid}/experiments/{eid}/outcome")
def record_outcome(rid: str, eid: str, req: ExperimentOutcomeRequest, request: Request) -> dict:
    r = store.get(rid)
    if r is None:
        raise _err(request, "not_found", "remnant not found", 404)
    exp = next((e for e in r.experiments if e.experiment_id == eid), None)
    if exp is None:
        raise _err(request, "not_found", "experiment not found", 404)
    if exp.status == "completed":
        # Duplicate outcome: idempotent write rejection (409), not silent overwrite.
        raise _err(request, "outcome_already_recorded", "experiment outcome already recorded and immutable", 409)
    if not (0.0 <= req.observed_value <= 1.0):
        raise _err(request, "invalid_observed_value", "observed value must be in [0, 1] (a ratio)", 422)
    apply_observed_outcome(r, exp, observed_value=req.observed_value)
    store.upsert(r)
    audit(
        "experiment.outcome",
        request_id=getattr(request.state, "request_id", None),
        remnant_id=rid,
        experiment_id=eid,
        observed_value=req.observed_value,
        verdict=exp.outcome,
        resolution_state=r.resolution_state.value,
    )
    return r.model_dump(mode="json")


@app.get("/api/v1/remnants/{rid}/belief")
def remnant_belief(rid: str, request: Request) -> dict:
    r = store.get(rid)
    if r is None:
        raise _err(request, "not_found", "remnant not found", 404)
    return {"remnant_id": rid, "belief": current_belief(r)}


@app.get("/api/v1/remnants/{rid}/provenance")
def remnant_provenance(rid: str, request: Request) -> dict:
    """Provenance, inspectable through the API: every expression + decision with
    its source, timestamp, and the evidence chain that produced it."""
    r = store.get(rid)
    if r is None:
        raise _err(request, "not_found", "remnant not found", 404)
    return {
        "remnant_id": rid,
        "expressions": [
            {
                "expression_id": e.expression_id,
                "text": e.text,
                "source": e.source.model_dump(mode="json"),
                "occurred_at": e.occurred_at.isoformat(),
            }
            for e in r.expressions
        ],
        "creator_decisions": [d.model_dump(mode="json") for d in r.creator_decisions],
        "state_transitions": r.state_transitions,
        "experiments": [
            {
                "experiment_id": e.experiment_id,
                "test": e.test,
                "metric": e.metric,
                "threshold_value": e.threshold_value,
                "threshold_operator": e.threshold_operator,
                "status": e.status,
                "observed_value": e.observed_value,
                "crossed_threshold": e.crossed_threshold,
                "outcome": e.outcome,
            }
            for e in r.experiments
        ],
    }


@app.post("/api/v1/observatory/run")
def observatory_run(request: Request) -> dict:
    """Run one autonomous observation pass (exposed for demo + tests). Returns
    surfaced candidates with action provenance. Consequential external actions
    are NOT executed by this endpoint — it recommends only. force=True: an
    explicit user/API-triggered run is not throttled by the autonomous cooldown."""
    if observatory is None:
        raise _err(request, "observatory_unavailable", "observatory not running", 503)
    surfaced = observatory.run_once(force=True)
    return {"surfaced": surfaced, "action_log": observatory.actions[-10:]}


@app.get("/api/v1/observatory/actions")
def observatory_actions(request: Request) -> dict:
    if observatory is None:
        raise _err(request, "observatory_unavailable", "observatory not running", 503)
    return {"actions": observatory.actions[-50:]}


@app.get("/api/v1/mind")
def mind_state() -> dict:
    st = minds_client.state()
    return {
        "ok": st.ok,
        "mind_id": st.mind_id,
        "name": st.name,
        "enabled": st.enabled,
        "cognition_balance": st.cognition_balance,
        "available": minds_client.available(),
        "error": st.error,  # EXPLICIT failure, never silent
    }


# --- back-compat: bare /api routes (same handlers) ------------------------------
# The v1 namespace is canonical; these aliases keep earlier docs/scripts working.

from fastapi import APIRouter  # noqa: E402

_alias = APIRouter(prefix="/api")


@_alias.get("/health")
def _health() -> dict:
    return health()


@_alias.get("/remnants")
def _list() -> list[dict]:
    return list_remnants(request=None)  # type: ignore[arg-type]


@_alias.post("/remnants")
def _create(req: CreateRemnantRequest) -> dict:
    return create_remnant(req, request=None)  # type: ignore[arg-type]


@_alias.post("/remnants/{rid}/expressions")
def _expr(rid: str, req: IngestExpressionRequest) -> dict:
    return add_expression(rid, req, request=None)  # type: ignore[arg-type]


@_alias.post("/remnants/{rid}/experiments/{eid}/outcome")
def _outcome(rid: str, eid: str, req: ExperimentOutcomeRequest) -> dict:
    return record_outcome(rid, eid, req, request=None)  # type: ignore[arg-type]


@_alias.get("/remnants/{rid}")
def _get(rid: str) -> dict:
    return get_remnant(rid, request=None)  # type: ignore[arg-type]


@_alias.post("/remnants/{rid}/decisions")
def _dec(rid: str, req: CreatorDecisionRequest) -> dict:
    return add_decision(rid, req, request=None)  # type: ignore[arg-type]


@_alias.post("/remnants/{rid}/experiments")
def _plan(rid: str) -> dict:
    return create_experiment(rid, request=None)  # type: ignore[arg-type]


@_alias.get("/remnants/{rid}/belief")
def _belief(rid: str) -> dict:
    return remnant_belief(rid, request=None)  # type: ignore[arg-type]


@_alias.get("/mind")
def _mind() -> dict:
    return mind_state()


app.include_router(_alias)