"""Knowledge — RAG engine & NBTC/NACO eligibility rules."""

from backend.knowledge.rag_engine import get_rag_engine
from backend.knowledge.eligibility_rules import get_all_rules, get_rules_by_category, get_rule_by_id

__all__ = ["get_rag_engine", "get_all_rules", "get_rules_by_category", "get_rule_by_id"]
