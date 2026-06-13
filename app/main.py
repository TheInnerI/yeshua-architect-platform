"""Yeshua Architect Platform — Main FastAPI application.

Free agent auditing + paid builds. Jesus-aligned AI agents.
Runs on :8080, behind Caddy reverse proxy.
"""

import json
from pathlib import Path
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from app.db import init_db, get_db, make_id
from app.models import AgentIntake
from app.scoring import evaluate_six_tests
from app.proxy import (
    score_via_poa, get_poa_receipt, get_poa_chain_length,
    check_poa_health, check_mio_health, observe_via_mio,
)
from app.agent_gen import generate_agent_prompt, generate_policy

# ── App setup ──────────────────────────────────────────────────

app = FastAPI(
    title="Yeshua Architect Platform",
    description="Free agent auditing + paid builds. Jesus-aligned AI agents.",
    version="0.1.0",
)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR.parent / "static")), name="static")

# Fresh Jinja2 environment
_jinja_env = Environment(
    loader=FileSystemLoader(str(BASE_DIR.parent / "templates")),
    autoescape=True,
)


def respond(template_name: str, context: dict, status_code: int = 200) -> HTMLResponse:
    """Render a Jinja2 template."""
    ctx = {"request": context.get("request")}
    for k, v in context.items():
        if k != "request":
            ctx[k] = v
    template = _jinja_env.get_template(template_name)
    content = template.render(**ctx)
    return HTMLResponse(content=content, status_code=status_code)


@app.on_event("startup")
async def startup():
    await init_db()


# ── Helpers ────────────────────────────────────────────────────

def _build_concept_text(intake: AgentIntake) -> str:
    """Build a single text from intake for scoring."""
    parts = [
        f"Agent name: {intake.agent_name}",
        f"Purpose: {intake.purpose}",
        f"Audience: {intake.audience or 'general'}",
        f"Problem solved: {intake.problem_solved or 'general assistance'}",
        f"Boundaries: {intake.boundaries or 'standard'}",
        f"Desired fruit: {intake.desired_fruit or 'clarity, wisdom, service'}",
        f"Monetization: {intake.monetization_model or 'none specified'}",
        f"Cognitive Solvency: {intake.solvency_model or 'none specified'}",
        f"Jesus anchor: {intake.jesus_anchor or 'general'}",
        f"Tools: {intake.tools_requested or 'standard'}",
        f"Tone: {intake.tone}",
    ]
    return ". ".join(parts)


# ── Public pages ───────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return respond("home.html", {"request": request})


@app.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works(request: Request):
    return respond("how-it-works.html", {"request": request})


@app.get("/five-tests", response_class=HTMLResponse)
async def five_tests(request: Request):
    return respond("five-tests.html", {"request": request})


@app.get("/examples", response_class=HTMLResponse)
async def examples(request: Request):
    return respond("examples.html", {"request": request})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return respond("pricing.html", {"request": request})


@app.get("/health", response_class=HTMLResponse)
async def health(request: Request):
    poa = await check_poa_health()
    mio = await check_mio_health()
    chain_len = await get_poa_chain_length() if poa == "connected" else 0
    return respond("health.html", {
        "request": request,
        "poa_status": poa,
        "mio_status": mio,
        "chain_length": chain_len,
    })


# ── Build / Intake ─────────────────────────────────────────────


@app.get("/build", response_class=HTMLResponse)
async def build_form(request: Request):
    return respond("build.html", {"request": request})


@app.post("/build/submit", response_class=HTMLResponse)
async def build_submit(
    request: Request,
    agent_name: str = Form(...),
    purpose: str = Form(...),
    audience: str = Form(default=""),
    problem_solved: str = Form(default=""),
    boundaries: str = Form(default=""),
    desired_fruit: str = Form(default=""),
    monetization_model: str = Form(default=""),
    jesus_anchor: str = Form(default=""),
    tools_requested: str = Form(default=""),
    tone: str = Form(default="warm and direct"),
):
    intake = AgentIntake(
        agent_name=agent_name,
        purpose=purpose,
        audience=audience,
        problem_solved=problem_solved,
        boundaries=boundaries,
        desired_fruit=desired_fruit,
        monetization_model=monetization_model,
        jesus_anchor=jesus_anchor,
        tools_requested=tools_requested,
        tone=tone,
    )

    concept_text = _build_concept_text(intake)
    five_result = evaluate_six_tests(concept_text)
    poa_result = await score_via_poa(concept_text)

    req_id = make_id("req_")
    audit_id = make_id("aud_")
    db = await get_db()

    await db.execute(
        """INSERT INTO agent_requests
           (id, agent_name, purpose, audience, problem_solved, boundaries,
            desired_fruit, monetization_model, jesus_anchor, tools_requested, tone, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (req_id, agent_name, purpose, audience, problem_solved, boundaries,
         desired_fruit, monetization_model, jesus_anchor, tools_requested, tone, "audited"),
    )

    correction_json = json.dumps(five_result.correction_notes) if five_result.correction_notes else ""

    await db.execute(
        """INSERT INTO agent_audits
           (id, agent_request_id, truth_score, neighbor_score, fruit_score,
            mammon_score, service_score, solvency_score, composite_five, grade, verdict,
            correction_notes, poa_receipt_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (audit_id, req_id, five_result.truth_score, five_result.neighbor_score,
         five_result.fruit_score, five_result.mammon_score, five_result.service_score,
         five_result.solvency_score, five_result.composite, poa_result.grade, five_result.verdict,
         correction_json, poa_result.receipt_id),
    )

    await db.commit()
    await db.close()

    # Convert Pydantic models to dicts for Jinja2
    five_dict = {
        "truth_score": five_result.truth_score,
        "neighbor_score": five_result.neighbor_score,
        "fruit_score": five_result.fruit_score,
        "mammon_score": five_result.mammon_score,
        "service_score": five_result.service_score,
        "solvency_score": five_result.solvency_score,
        "composite": five_result.composite,
        "verdict": five_result.verdict,
        "correction_notes": five_result.correction_notes or {},
    }

    # Generate deliverable package
    from app.agent_gen import generate_deliverable_package
    deliverable = generate_deliverable_package(intake, five_dict, poa_result.receipt_id)

    # Save agent files
    agent_dir = BASE_DIR.parent / "data" / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_file = agent_dir / f"{req_id}.md"
    policy_file = agent_dir / f"{req_id}_policy.json"
    agent_file.write_text(deliverable["agent_md"])
    policy_file.write_text(deliverable["policy_json"])

    # Store in agents table (reopen DB since it was closed above)
    db = await get_db()
    await db.execute(
        """INSERT INTO agents (id, agent_request_id, name, system_prompt, tier, delivery_path, policy_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        (make_id("agt_"), req_id, agent_name, deliverable["agent_md"], "starter", str(agent_file), deliverable["policy_json"]),
    )
    await db.commit()
    await db.close()

    # Feed to MIO (non-blocking, ignore errors)
    try:
        await observe_via_mio(req_id, {
            "event": "intake_submitted",
            "agent_name": agent_name,
            "verdict": five_result.verdict,
            "composite": five_result.composite,
        })
    except Exception:
        pass

    return respond("build_status.html", {
        "request": request,
        "agent_name": agent_name,
        "five_result": five_dict,
        "poa_grade": poa_result.grade,
        "poa_receipt_id": poa_result.receipt_id,
        "req_id": req_id,
        "agent_file": str(agent_file),
        "policy_file": str(policy_file),
    })


# ── Download Agent Package ──────────────────────────────────────

from app.package_generator import create_agent_zip_package
from fastapi.responses import Response


@app.get("/download/package/{req_id}")
async def download_package(request: Request, req_id: str, tier: str = "starter"):
    """Download the agent's .zip package."""
    db = await get_db()
    agent_row = await db.execute("SELECT * FROM agents WHERE agent_request_id = ?", (req_id,))
    agent = await agent_row.fetchone()
    if not agent:
        await db.close()
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get audit results
    audit_row = await db.execute("SELECT * FROM agent_audits WHERE agent_request_id = ?", (req_id,))
    audit = await audit_row.fetchone()
    await db.close()

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Reconstruct verdict dict
    verdict = {
        "truth_score": audit["truth_score"],
        "neighbor_score": audit["neighbor_score"],
        "fruit_score": audit["fruit_score"],
        "mammon_score": audit["mammon_score"],
        "service_score": audit["service_score"],
        "solvency_score": audit.get("solvency_score", 0),
        "composite": audit["composite_five"],
        "verdict": audit["verdict"],
        "correction_notes": {},
    }

    if audit["correction_notes"]:
        try:
            verdict["correction_notes"] = json.loads(audit["correction_notes"])
        except Exception:
            pass

    # Reconstruct intake
    intake = AgentIntake(
        agent_name=agent["name"],
        purpose=agent_row["purpose"] if hasattr(agent_row, "purpose") else "General assistant",
        audience=None,
        problem_solved=None,
        boundaries=None,
        desired_fruit=None,
        monetization_model=None,
        jesus_anchor=None,
        tools_requested=None,
        tone="warm and direct",
    )

    # Generate zip
    zip_bytes = create_agent_zip_package(
        intake=intake,
        verdict=verdict,
        poa_receipt_id=audit.get("poa_receipt_id", ""),
        tier=tier,
    )

    # Return as download
    safe_name = agent["name"].lower().replace(" ", "-")
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={safe_name}-agent.zip"},
    )


# ── Agents list ────────────────────────────────────────────────


@app.get("/agents", response_class=HTMLResponse)
async def agents_list(request: Request):
    db = await get_db()
    rows = await db.execute(
        "SELECT * FROM agent_requests WHERE status='delivered' ORDER BY created_at DESC LIMIT 50"
    )
    agents = await rows.fetchall()
    await db.close()
    return respond("agents.html", {"request": request, "agents": agents})


# ── Agent detail ───────────────────────────────────────────────


@app.get("/agents/{agent_id}", response_class=HTMLResponse)
async def agent_detail(request: Request, agent_id: str):
    db = await get_db()
    req_row = await db.execute("SELECT * FROM agent_requests WHERE id = ?", (agent_id,))
    req = await req_row.fetchone()
    if not req:
        await db.close()
        raise HTTPException(status_code=404, detail="Agent not found")
    audit_row = await db.execute("SELECT * FROM agent_audits WHERE agent_request_id = ?", (agent_id,))
    audit = await audit_row.fetchone()
    await db.close()

    correction_notes = {}
    if audit and audit["correction_notes"]:
        try:
            correction_notes = json.loads(audit["correction_notes"])
        except Exception:
            pass

    return respond("agent_detail.html", {
        "request": request,
        "agent": req,
        "audit": audit,
        "correction_notes": correction_notes,
    })


# ── Dashboard ──────────────────────────────────────────────────


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    db = await get_db()
    total_reqs = (await (await db.execute("SELECT COUNT(*) FROM agent_requests")).fetchone())[0]
    total_audited = (await (await db.execute("SELECT COUNT(*) FROM agent_audits")).fetchone())[0]
    approved = (await (await db.execute("SELECT COUNT(*) FROM agent_audits WHERE verdict IN ('approved', 'good_fruit')")).fetchone())[0]
    rejected = (await (await db.execute("SELECT COUNT(*) FROM agent_audits WHERE verdict = 'rejected'")).fetchone())[0]
    recent = await (await db.execute("SELECT * FROM agent_requests ORDER BY created_at DESC LIMIT 10")).fetchall()
    await db.close()

    poa = await check_poa_health()
    mio = await check_mio_health()
    chain_len = await get_poa_chain_length() if poa == "connected" else 0

    return respond("dashboard.html", {
        "request": request,
        "stats": {
            "total_requests": total_reqs,
            "total_audited": total_audited,
            "approved": approved,
            "rejected": rejected,
        },
        "recent": recent,
        "poa_status": poa,
        "mio_status": mio,
        "chain_length": chain_len,
    })


# ── Receipt view ───────────────────────────────────────────────


@app.get("/receipts/{receipt_id}", response_class=HTMLResponse)
async def view_receipt(request: Request, receipt_id: str):
    receipt = await get_poa_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return respond("receipt.html", {"request": request, "receipt": receipt})


# ── Download agent file ────────────────────────────────────────

from fastapi.responses import FileResponse

@app.get("/download/agent/{req_id}")
async def download_agent(req_id: str):
    """Download the agent .md file."""
    agent_file = BASE_DIR.parent / "data" / "agents" / f"{req_id}.md"
    if not agent_file.exists():
        raise HTTPException(status_code=404, detail="Agent file not found")
    return FileResponse(str(agent_file), filename=f"{req_id}_agent.md", media_type="text/markdown")

@app.get("/download/policy/{req_id}")
async def download_policy(req_id: str):
    """Download the policy JSON file."""
    policy_file = BASE_DIR.parent / "data" / "agents" / f"{req_id}_policy.json"
    if not policy_file.exists():
        raise HTTPException(status_code=404, detail="Policy file not found")
    return FileResponse(str(policy_file), filename=f"{req_id}_policy.json", media_type="application/json")


# ── Live Agent Chat ─────────────────────────────────────────────

from app.agent_service import get_agent_service, MODELS, TIER_MODELS


@app.post("/api/chat/{req_id}")
async def chat_with_agent(req_id: str, request: Request):
    """Send a message to a live agent and get a response."""
    body = await request.json()
    user_message = body.get("message", "")
    model_key = body.get("model", "owl-alpha")
    history = body.get("history", [])

    if not user_message:
        return JSONResponse({"error": "Message required"}, status_code=400)

    # Get the agent's system prompt
    db = await get_db()
    agent_row = await db.execute("SELECT * FROM agents WHERE agent_request_id = ?", (req_id,))
    agent = await agent_row.fetchone()
    await db.close()

    if not agent:
        return JSONResponse({"error": "Agent not found"}, status_code=404)

    agent_prompt = agent["system_prompt"]

    # Check if model is allowed for tier (default free)
    tier = "free"
    allowed_models = TIER_MODELS.get(tier, TIER_MODELS["free"])
    if model_key not in allowed_models:
        model_key = allowed_models[0]

    # Call OpenRouter
    service = get_agent_service()
    if not service.is_configured:
        return JSONResponse({"error": "OpenRouter not configured"}, status_code=500)

    try:
        result = await service.chat(
            agent_prompt=agent_prompt,
            user_message=user_message,
            model_key=model_key,
            conversation_history=history,
        )
        return JSONResponse({
            "response": result["response"],
            "model": result["model"],
        })
    except Exception as e:
        logger.error("Chat error: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/models")
async def get_models():
    """Get available models."""
    service = get_agent_service()
    models = service.get_available_models("free")
    return JSONResponse({"models": models})


@app.get("/chat/{req_id}")
async def chat_page(request: Request, req_id: str):
    """Live agent chat page."""
    db = await get_db()
    agent_row = await db.execute("SELECT * FROM agents WHERE agent_request_id = ?", (req_id,))
    agent = await agent_row.fetchone()
    await db.close()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return respond("chat.html", {
        "request": request,
        "agent": agent,
        "req_id": req_id,
    })


# ── CLI entry point ────────────────────────────────────────────

def main():
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)


if __name__ == "__main__":
    main()
