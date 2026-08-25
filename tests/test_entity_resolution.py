import pandas as pd
from src.entity_resolution import resolve_agents


def test_agent_resolution_prefers_employee_code():
    agents = pd.DataFrame({"agent_id": ["a1"], "employee_code": ["e1"], "agent_name": ["Name"], "vendor_id": ["v1"], "joined_at": ["2026-01-01"]})
    clean, mapping = resolve_agents(agents)
    assert clean["canonical_agent_id"].iloc[0] == "EMP::e1"
    assert mapping["resolution_confidence"].iloc[0] == "HIGH"
