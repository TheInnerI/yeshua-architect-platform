"""Pydantic models for Yeshua Architect Platform."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AgentIntake(BaseModel):
    """12-question intake form (now 13 with Cognitive Solvency)."""
    agent_name: str = Field(..., min_length=1, max_length=200, description="What do you want to call this agent?")
    purpose: str = Field(..., min_length=10, description="What do you want this agent to help with?")
    audience: Optional[str] = Field(None, description="Who will this agent serve?")
    problem_solved: Optional[str] = Field(None, description="What problem does it solve?")
    boundaries: Optional[str] = Field(None, description="What should it never do?")
    desired_fruit: Optional[str] = Field(None, description="What kind of fruit should it produce?")
    monetization_model: Optional[str] = Field(None, description="How will this agent make money, save time, or create value?")
    solvency_model: Optional[str] = Field(None, description="Can this agent fund its own cognition? What is its revenue loop?")
    jesus_anchor: Optional[str] = Field(None, description="What Jesus teaching should anchor this agent?")
    tools_requested: Optional[str] = Field(None, description="What tools should it use?")
    tone: Optional[str] = Field("warm and direct", description="What tone should it speak with?")


class ScoreRequest(BaseModel):
    """Request to score an agent concept via PoA API."""
    output: str = Field(..., min_length=1, description="The agent concept to score")
    observer_id: str = Field("yeshua-platform", description="Observer ID for receipt")
    persist: bool = Field(True, description="Store receipt on chain")


class ScoreResponse(BaseModel):
    """Response from PoA API scoring."""
    receipt_id: str
    composite: float
    grade: str
    scores: dict = {}
    constraints: dict = {}
    receipt_hash: str = ""
    persisted: bool = False
    chain_index: Optional[int] = None


class FiveTestVerdict(BaseModel):
    """Six Test evaluation result (kept name for backward compatibility)."""
    truth_score: float
    neighbor_score: float
    fruit_score: float
    mammon_score: float
    service_score: float
    solvency_score: float = 0.0
    composite: float
    verdict: str  # approved / needs_correction / rejected / good_fruit
    correction_notes: dict = {}  # test_name -> note


class AgentAuditRow(BaseModel):
    """Audit result for display."""
    id: str
    agent_request_id: str
    truth_score: float
    neighbor_score: float
    fruit_score: float
    mammon_score: float
    service_score: float
    composite_five: float
    grade: str = ""
    verdict: str
    correction_notes: str = ""
    poa_receipt_id: str = ""
    created_at: str


class AgentRequestRow(BaseModel):
    """Agent request for display."""
    id: str
    agent_name: str
    purpose: str
    audience: str = ""
    status: str
    tier: str = "free"
    created_at: str


class HealthResponse(BaseModel):
    """System health check."""
    status: str
    platform: str
    version: str
    poa_api: str
    mio_api: str
    chain_length: int = 0
