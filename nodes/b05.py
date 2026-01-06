import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState
from utils.config import get_config


def b05(state: AgentState):
    """Return partial state with BO5 results (no in-place mutation)."""
    metrics = state.get("raw_metrics", {})
    onboarding = metrics.get("onboarding", {})
    perf = metrics.get("performance", {})
    dc_data = metrics.get("dc_activity", {})

    config = get_config()
    bo_conf = next((b for b in config.get("business_objectives", []) if b["bo_code"] == "BO5"), {})
    factors = {f["factor_code"]: f for f in bo_conf.get("factors", [])}

    f_meet_conf = factors.get("B5A", {}).get("benchmark", {})
    mult_pl = f_meet_conf.get("pl_dcs_multiplier", 0.25)
    cap_meetings = f_meet_conf.get("cap", 6)

    pl_active_last_q = perf.get("pl_active_dcs_last_quarter", 20)
    benchmark_meet = min(pl_active_last_q * mult_pl, cap_meetings)
    actual_meet = metrics.get("meetings", {}).get("farmer_meetings_mtd", 0)
    ratio_meet = actual_meet / benchmark_meet if benchmark_meet > 0 else 0

    f_new_conf = factors.get("B5B", {}).get("benchmark", {})
    mult_dcs = f_new_conf.get("total_dcs_multiplier", 0.02)
    min_floor = f_new_conf.get("min_floor", 1)

    total_dcs = dc_data.get("total_dcs", 20)
    benchmark_new = max(min_floor, total_dcs * mult_dcs)
    actual_new = onboarding.get("new_retailers_mtd", 0)
    ratio_new = actual_new / benchmark_new if benchmark_new > 0 else 0

    weights = bo_conf.get("combine_logic", {}).get("weights", {"B5A": 0.6, "B5B": 0.4})
    wa = weights.get("B5A", 0.6)
    wb = weights.get("B5B", 0.4)

    final_ratio = (ratio_meet * wa) + (ratio_new * wb)

    return {"bo_results": {"BO5": {"ratio": final_ratio, "meeting_ratio": ratio_meet, "onboarding_ratio": ratio_new}}}