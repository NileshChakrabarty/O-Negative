#!/usr/bin/env python3
"""
O-Negative Orchestrator Agent

A clinical agent system that:
1. Parses donation requests (blood group, location, medical context)
2. Consults RAG for eligibility rules (NBTC/NACO/WHO)
3. Queries live data (blood banks, live donor roster)
4. References memory (donor response reliability, bank reputation)
5. Synthesizes clinical recommendations via Google Gemini (gemini-3.6-flash)
   with transparent step-by-step reasoning.
"""

import json
from typing import TypedDict, Any, List, Dict, Optional
from enum import Enum

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

# Data Layer
try:
    from backend.data_layer.blood_banks import list_nearby_banks
    from backend.data_layer.donor_registry import check_donor_availability
except ImportError:
    print("Note: Data layer not available in path")
    def list_nearby_banks(location: str, radius_km: float = 10) -> dict:
        return {"count": 0, "banks": []}
    def check_donor_availability(blood_group: str, location: str, radius_km: float = 15) -> dict:
        return {"count": 0, "donors": []}

# RAG Knowledge Base
try:
    from backend.knowledge.rag_engine import get_rag_engine
    rag_engine = get_rag_engine()
except Exception as e:
    print(f"Note: RAG engine not available: {e}")
    rag_engine = None

# Persistent Memory
try:
    from backend.memory.memory_db import get_memory_db
    memory_db = get_memory_db()
except Exception as e:
    print(f"Note: Memory DB not available: {e}")
    memory_db = None

# Gemini LLM Setup
gemini_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"✓ Google Gemini client initialized ({GEMINI_MODEL})")
    except Exception as e:
        print(f"⚠️ Could not initialize Gemini client: {e}")


# ============================================================================
# State Schema
# ============================================================================

class AgentState(TypedDict):
    """State passed through agent reasoning pipeline."""
    query: str
    parsed_request: Dict[str, Any]
    eligible_donors: List[Dict[str, Any]]
    eligible_banks: List[Dict[str, Any]]
    eligibility_context: str
    recommendation: str
    reasoning_trail: List[Dict[str, Any]]
    confidence_score: float


class RequestType(Enum):
    """Types of requests the agent handles."""
    DONOR_ELIGIBILITY = "donor_eligibility"  # "Can I donate on antibiotics?"
    REQUEST_BLOOD = "request_blood"          # "I need O- blood urgently in Sonipat"
    DONOR_STATUS = "donor_status"            # "Where can I donate?"
    BLOOD_INVENTORY = "blood_inventory"      # "Do you have O- available?"


# ============================================================================
# Reasoning Nodes
# ============================================================================

def parse_request(state: AgentState) -> AgentState:
    """Parse user's natural language query into structured medical context."""
    query = state["query"].lower()
    reasoning = []
    
    request_type = RequestType.DONOR_ELIGIBILITY
    blood_group = None
    location = None
    context = ""
    
    # Blood request detection
    if ("need" in query or "urgent" in query or "require" in query or "looking for" in query) and ("blood" in query or "donor" in query):
        request_type = RequestType.REQUEST_BLOOD
        reasoning.append("Detected: blood request (urgent)")
    elif "donate" in query or "donation" in query or "eligible" in query or "can i" in query:
        request_type = RequestType.DONOR_ELIGIBILITY
        reasoning.append("Detected: donor eligibility question")
    
    # Extract blood group if mentioned
    for bg in ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]:
        if bg.lower() in query:
            blood_group = bg
            reasoning.append(f"Extracted blood group: {bg}")
            break
            
    # Extract location
    locations = ["sonipat", "delhi", "panipat", "haryana", "punjab", "noida", "gurgaon"]
    for loc in locations:
        if loc in query:
            location = loc.capitalize()
            reasoning.append(f"Extracted location: {location}")
            break
            
    # Extract clinical context
    if "antibiotic" in query or "amoxicillin" in query or "ciprofloxacin" in query:
        context = "on_medication (antibiotics)"
        reasoning.append("Context: donor on antibiotics (requires 48-72 hr deferral)")
    elif "month ago" in query or "weeks ago" in query or "recently" in query:
        context = "recent_donation"
        reasoning.append("Context: recent donation (requires minimum 12-week interval)")
    elif "pregnant" in query or "pregnancy" in query:
        context = "pregnancy"
        reasoning.append("Context: pregnancy-related donation inquiry")
    elif "tattoo" in query or "piercing" in query:
        context = "tattoo_piercing"
        reasoning.append("Context: recent tattoo/piercing (6-12 month deferral)")
    elif "alcohol" in query:
        context = "alcohol"
        reasoning.append("Context: alcohol consumption (24 hr deferral)")

    state["parsed_request"] = {
        "request_type": request_type.value,
        "blood_group": blood_group or "O-",
        "location": location or "Sonipat",
        "context": context
    }
    
    state["reasoning_trail"] = [{"step": "parse_request", "reasoning": reasoning}]
    return state


def retrieve_eligibility_rules(state: AgentState) -> AgentState:
    """Retrieve official NBTC/NACO eligibility guidelines via RAG."""
    reasoning = []
    eligibility_context = ""
    
    if not rag_engine:
        reasoning.append("RAG engine not active, using default clinical guidelines")
        state["reasoning_trail"].append({"step": "retrieve_eligibility_rules", "reasoning": reasoning})
        return state
        
    parsed = state["parsed_request"]
    context_str = parsed.get("context", "")
    query_str = state["query"]
    
    rag_query = f"{query_str} {context_str}"
    reasoning.append(f"RAG search query: '{rag_query}'")
    
    retrieved = rag_engine.retrieve(rag_query, k=3)
    reasoning.append(f"Retrieved {len(retrieved)} relevant clinical rules from ChromaDB vector index")
    
    if retrieved:
        formatted_rules = []
        for r in retrieved:
            formatted_rules.append(f"• [{r['source']}] {r['text']} (Relevance: {r.get('relevance_score', 0):.2f})")
            reasoning.append(f"Matched rule: {r.get('id', 'rule')} from {r.get('source', 'NBTC')}")
        eligibility_context = "\n".join(formatted_rules)
    
    state["eligibility_context"] = eligibility_context
    state["reasoning_trail"].append({"step": "retrieve_eligibility_rules", "reasoning": reasoning})
    return state


def query_live_data(state: AgentState) -> AgentState:
    """Query live blood banks and active donor registry."""
    reasoning = []
    parsed = state["parsed_request"]
    location = parsed.get("location", "Sonipat")
    blood_group = parsed.get("blood_group", "O-")
    
    # Live blood banks
    banks_resp = list_nearby_banks(location, radius_km=25)
    banks = banks_resp.get("banks", [])
    reasoning.append(f"Queried data.gov.in directory: found {len(banks)} blood banks within 25km of {location}")
    for b in banks[:2]:
        reasoning.append(f"  → {b['bank_name']} ({b['distance_km']:.1f} km away, Contact: {b['contact']})")
        
    # Live donor availability
    donors_resp = check_donor_availability(blood_group, location, radius_km=25)
    donors = donors_resp.get("donors", [])
    reasoning.append(f"Queried donor availability DB: found {len(donors)} available {blood_group} donors in {location}")
    
    state["eligible_banks"] = banks
    state["eligible_donors"] = donors
    state["reasoning_trail"].append({"step": "query_live_data", "reasoning": reasoning})
    return state


def rank_candidates(state: AgentState) -> AgentState:
    """Rank donors using persistent memory (reliability scoring)."""
    reasoning = []
    donors = state.get("eligible_donors", [])
    
    if not donors:
        reasoning.append("No live candidate donors found to rank")
        state["reasoning_trail"].append({"step": "rank_candidates", "reasoning": reasoning})
        return state
        
    if memory_db:
        ranked = memory_db.rank_donors(donors)
        reasoning.append(f"Memory-based ranking applied across {len(ranked)} donors:")
        for d in ranked:
            rate = d.get("reliability_rate", 0.5) * 100
            count = d.get("response_count", 0)
            reasoning.append(f"  → {d['donor_id']}: {rate:.0f}% historical response rate ({count} past alerts)")
        state["eligible_donors"] = ranked
    else:
        reasoning.append(f"Memory DB unavailable; maintaining default order for {len(donors)} donors")
        
    state["reasoning_trail"].append({"step": "rank_candidates", "reasoning": reasoning})
    return state


def generate_recommendation(state: AgentState) -> AgentState:
    """Generate final clinical-grade response using Gemini LLM with fallback."""
    reasoning = []
    parsed = state["parsed_request"]
    request_type = parsed.get("request_type")
    blood_group = parsed.get("blood_group", "O-")
    location = parsed.get("location", "Sonipat")
    donors = state.get("eligible_donors", [])
    banks = state.get("eligible_banks", [])
    eligibility_context = state.get("eligibility_context", "")
    
    recommendation = ""
    confidence = 0.85
    
    # Try Gemini first if available
    if gemini_client:
        try:
            prompt = f"""You are O-Negative, India's AI-driven blood coordination clinical assistant.
The user asked: "{state['query']}"

Context & Live System State:
- Request Type: {request_type}
- Target Blood Group: {blood_group}
- Target Location: {location}
- Clinical Eligibility Rules from NBTC/NACO:
{eligibility_context if eligibility_context else "No specific restriction flagged."}

- Nearby Verified Blood Banks (Live Data):
{json.dumps([{ 'name': b['bank_name'], 'distance_km': b['distance_km'], 'contact': b['contact'], 'address': b['address'] } for b in banks[:3]], indent=2)}

- Live Ranked Donors (Memory Reliability):
{json.dumps([{ 'donor_id': d['donor_id'], 'blood_group': d['blood_group'], 'reliability': f"{d.get('reliability_rate', 0.5)*100:.0f}%" } for d in donors[:3]], indent=2)}

Instructions:
1. Address the user's situation directly, empathetically, and authoritatively.
2. If this is an eligibility question (e.g. antibiotics, donation interval, fever), state clearly whether they or their relative can donate, cite the exact waiting period (e.g., wait 48-72 hours after completing antibiotics; wait 12 weeks/3 months between whole blood donations) referencing NBTC/NACO guidelines.
3. If this is an urgent blood request, list the top verified donors and nearby blood banks with contact details and distances.
4. Keep the response concise, clear, and formatted nicely in markdown.
"""
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            recommendation = response.text.strip()
            reasoning.append(f"Synthesized clinical response via {GEMINI_MODEL}")
            confidence = 0.95
        except Exception as e:
            reasoning.append(f"Gemini generation fallback triggered ({e})")
            recommendation = ""

    # Deterministic fallback if Gemini was unavailable or failed
    if not recommendation:
        if request_type == "donor_eligibility":
            recommendation = f"""### Blood Donation Eligibility Guidance (NBTC / NACO Guidelines)

{eligibility_context if eligibility_context else "Donors must generally be 18-65 years old, weigh at least 45kg, and be in good general health."}

**Key Clinical Notes:**
• **Antibiotics:** Wait **48 to 72 hours** after completing your antibiotic course and ensuring you are symptom-free before donating blood.
• **Donation Interval:** Male and female whole blood donors must wait at least **12 weeks (3 months)** between whole blood donations.
• Always inform the medical officer at the blood bank about recent medications.
"""
            reasoning.append("Generated rule-based eligibility guidance")
            confidence = 0.85
        elif request_type == "request_blood":
            donor_list_str = ""
            if donors:
                donor_list_str = "#### Top Ranked Available Donors (by historical reliability):\n"
                for i, d in enumerate(donors[:3], 1):
                    rate = d.get("reliability_rate", 0.5) * 100
                    donor_list_str += f"{i}. **{d['donor_id']}** ({d['blood_group']}) — {rate:.0f}% past response rate\n"
            else:
                donor_list_str = "No verified individual donors currently registered for this blood group in the immediate area.\n"

            bank_list_str = ""
            if banks:
                bank_list_str = f"#### Nearby Blood Banks in {location}:\n"
                for i, b in enumerate(banks[:3], 1):
                    bank_list_str += f"{i}. **{b['bank_name']}** — {b['distance_km']:.1f} km away | 📞 {b['contact']}\n"

            recommendation = f"""### Urgent Blood Request Coordination: {blood_group} in {location}

{donor_list_str}
{bank_list_str}
*To alert these donors immediately, use the notification hub.*
"""
            reasoning.append("Generated rule-based urgent coordination guidance")
            confidence = 0.90
        else:
            recommendation = "Please specify your blood coordination inquiry, such as eligibility questions ('Can I donate on antibiotics?') or urgent requirements ('Need O- blood in Sonipat')."
            confidence = 0.70

    state["recommendation"] = recommendation
    state["confidence_score"] = confidence
    state["reasoning_trail"].append({
        "step": "generate_recommendation",
        "reasoning": reasoning,
        "confidence": confidence
    })
    
    # Log request in persistent memory
    if memory_db:
        try:
            memory_db.log_request(
                blood_group=blood_group,
                location=location,
                raw_query=state["query"],
                reasoning_trail=state["reasoning_trail"]
            )
        except Exception as e:
            print(f"Failed to log request: {e}")

    return state


# ============================================================================
# Main Orchestrator Runner
# ============================================================================

def run_agent(query: str) -> Dict[str, Any]:
    """
    Execute full 5-step O-Negative reasoning state machine.
    
    Returns:
        {
            "recommendation": str,
            "reasoning_trail": List[Dict],
            "confidence": float,
            "parsed_request": Dict
        }
    """
    state: AgentState = {
        "query": query,
        "parsed_request": {},
        "eligible_donors": [],
        "eligible_banks": [],
        "eligibility_context": "",
        "recommendation": "",
        "reasoning_trail": [],
        "confidence_score": 0.0
    }
    
    state = parse_request(state)
    state = retrieve_eligibility_rules(state)
    state = query_live_data(state)
    state = rank_candidates(state)
    state = generate_recommendation(state)
    
    return {
        "recommendation": state["recommendation"],
        "reasoning_trail": state["reasoning_trail"],
        "confidence": state["confidence_score"],
        "parsed_request": state["parsed_request"],
        "eligible_donors": state["eligible_donors"],
        "eligible_banks": state["eligible_banks"]
    }


if __name__ == "__main__":
    demo_query = "My cousin gave blood a month ago and is on antibiotics right now. Can he donate again?"
    print(f"\nRunning test query: '{demo_query}'\n")
    res = run_agent(demo_query)
    print("Recommendation:\n", res["recommendation"])
    print("\nReasoning Trail:")
    for step in res["reasoning_trail"]:
        print(f"[{step['step']}]")
        for r in step.get("reasoning", []):
            print(f"  • {r}")
