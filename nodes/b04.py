import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState
from utils.config import get_config


def b04(state: AgentState):
    """Return partial state with BO4 results (no in-place mutation)."""
    metrics = state.get("raw_metrics", {})
    perf = metrics.get("performance", {})
    dc_data = metrics.get("dc_activity", {})

    config = get_config()
    bo_conf = next((b for b in config.get("business_objectives", []) if b["bo_code"] == "BO4"), {})
    factors = {f["factor_code"]: f for f in bo_conf.get("factors", [])}

    f_vel_conf = factors.get("B4A", {}).get("benchmark", {})
    vel_mult = f_vel_conf.get("multiplier", 1.15)

    last_month_sales = perf.get("last_month_sales", 1)
    benchmark_vel = last_month_sales * vel_mult
    actual_sales = perf.get("mtd_sales_value", 0)

    ratio_vel = actual_sales / benchmark_vel if benchmark_vel > 0 else 0
    ratio_vel = min(ratio_vel, 1.5)

    f_spr_conf = factors.get("B4B", {}).get("benchmark", {})
    mult_total = f_spr_conf.get("total_dcs_multiplier", 0.6)
    mult_active = f_spr_conf.get("active_dcs_multiplier", 1.2)

    total_dcs = dc_data.get("total_dcs", 10)
    last_month_active = perf.get("last_month_active_dcs", 5)

    benchmark_spread = min(total_dcs * mult_total, last_month_active * mult_active)
    actual_spread = perf.get("unique_transacting_dcs_mtd", 0)

    ratio_spread = actual_spread / benchmark_spread if benchmark_spread > 0 else 0
    ratio_spread = min(ratio_spread, 1.5)

    final_ratio = ratio_vel * ratio_spread

    return {"bo_results": {"BO4": {"ratio": final_ratio, "velocity": ratio_vel, "spread": ratio_spread}}}