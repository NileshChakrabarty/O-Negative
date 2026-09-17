"""Query route — runs the AI agent pipeline."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agent.orchestrator import run_agent

router = APIRouter()


class BloodRequest(BaseModel):
    query: str
    location: str = "Sonipat"
    blood_group: Optional[str] = "O-"
    user_type: str = "patient"
    user_phone_last_4: Optional[str] = None


class AgentResponse(BaseModel):
    recommendation: str
    confidence: float
    reasoning_trail: List[Dict[str, Any]]
    parsed_request: Dict[str, Any]
    eligible_donors: Optional[List[Dict[str, Any]]] = []
    eligible_banks: Optional[List[Dict[str, Any]]] = []


@router.post("/api/query", response_model=AgentResponse)
async def query_agent(request: BloodRequest):
    """Run blood coordination agent through 5-step clinical reasoning."""
    try:
        result = run_agent(request.query)
        return AgentResponse(
            recommendation=result["recommendation"],
            confidence=result["confidence"],
            reasoning_trail=result["reasoning_trail"],
            parsed_request=result["parsed_request"],
            eligible_donors=result.get("eligible_donors", []),
            eligible_banks=result.get("eligible_banks", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
