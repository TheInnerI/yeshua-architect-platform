"""Proxy to PoA Engine API (:8000) and MIO Observer (:8787)."""

import httpx
from typing import Optional
from app.models import ScoreResponse

POA_BASE = "http://localhost:8000"
MIO_BASE = "http://localhost:8787"

# PoA API key — must match the key configured in poa-api.env
# This is the free tier key that ships with the PoA API
POA_API_KEY = "poa_free_public"


async def score_via_poa(text: str, observer_id: str = "yeshua-platform", persist: bool = True) -> ScoreResponse:
    """Send agent concept to PoA Engine for 7-constraint scoring."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{POA_BASE}/score", json={
                "output": text,
                "observer_id": observer_id,
                "persist": persist,
                "engine": "dynamic",
            }, headers={
                "X-API-Key": POA_API_KEY,
            })
            if resp.status_code == 200:
                data = resp.json()
                return ScoreResponse(
                    receipt_id=data.get("receipt_id", ""),
                    composite=data.get("composite", 0.0),
                    grade=data.get("grade", "F"),
                    scores=data.get("scores", {}),
                    constraints=data.get("constraints", {}),
                    receipt_hash=data.get("receipt_hash", ""),
                    persisted=data.get("persist", False),
                    chain_index=data.get("chain_index"),
                )
    except Exception as e:
        pass

    # Fallback if PoA is unavailable
    return ScoreResponse(
        receipt_id="unavailable",
        composite=0.0,
        grade="N/A",
        scores={},
        constraints={},
        persisted=False,
    )


async def get_poa_receipt(receipt_id: str) -> Optional[dict]:
    """Fetch a receipt from PoA chain."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{POA_BASE}/receipt/{receipt_id}")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


async def get_poa_chain_length() -> int:
    """Get current chain length from PoA."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{POA_BASE}/health")
            if resp.status_code == 200:
                return resp.json().get("chain_length", 0)
    except Exception:
        pass
    return 0


async def check_poa_health() -> str:
    """Check if PoA API is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{POA_BASE}/health")
            if resp.status_code == 200:
                return "connected"
    except Exception:
        pass
    return "unavailable"


async def check_mio_health() -> str:
    """Check if MIO Observer is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{MIO_BASE}/health")
            if resp.status_code == 200:
                return "connected"
    except Exception:
        pass
    return "unavailable"


async def observe_via_mio(agent_request_id: str, payload: dict) -> Optional[str]:
    """Feed an event into MIO Observer."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{MIO_BASE}/upload", json={
                "agent_request_id": agent_request_id,
                "payload": payload,
            })
            if resp.status_code == 200:
                data = resp.json()
                return data.get("observation_id")
    except Exception:
        pass
    return None
