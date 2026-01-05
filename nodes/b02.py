import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState


def b02(state: AgentState):
    metrics = state.get("raw_metrics", {})
    dc_data = metrics.get("dc_activity", {})

    # BO2: DC CHECK-INS (Coverage × Effort)
    coverage = dc_data.get("unique_dcs_visited", 0) / max(dc_data.get("total_dcs", 1), 1)
    effort = dc_data.get("check_ins_count", 0) / max(dc_data.get("expected_check_ins", 1), 1)
    ratio = coverage * effort

    state.setdefault("bo_results", {})["BO2"] = {"ratio": ratio, "coverage": coverage, "effort": effort}
    return state
