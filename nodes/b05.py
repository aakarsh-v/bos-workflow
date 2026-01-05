import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState


def b05(state: AgentState):
    metrics = state.get("raw_metrics", {})
    onboarding = metrics.get("onboarding", {})

    # BO5: MARKET DEVELOPMENT (Enablement + Expansion)
    new_retailers_mtd = onboarding.get("new_retailers_mtd", 0)
    new_retailers_last_month = onboarding.get("new_retailers_last_month", 0)
    enablement = new_retailers_mtd / max(new_retailers_last_month, 1)
    expansion = new_retailers_mtd / max(onboarding.get("new_retailers_last12m", 1), 1)
    ratio = (enablement + expansion) / 2.0

    state.setdefault("bo_results", {})["BO5"] = {"ratio": ratio, "enablement": enablement, "expansion": expansion}
    return state
