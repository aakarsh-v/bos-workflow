import argparse
import json
import logging
import os
from dotenv import load_dotenv

from nodes.resolve_priority import prioritize
from nodes.b01 import b01
from nodes.b02 import b02
from nodes.b03 import b03
from nodes.b04 import b04
from nodes.b05 import b05
from nodes.merge_bo_results import merge_bo_results

# load env for optional tracing integrations (e.g. LANGSMITH_API_KEY)
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("workflow-mock")


def _save_state(state: dict, thread_id: str, path: str = None):
    """Persist a JSON snapshot of the workflow state for debugging and resume."""
    if path is None:
        path = f"mock_state_{thread_id}.json"
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
        logger.info("Saved state snapshot to %s", path)
    except Exception as e:
        logger.warning("Failed to save state snapshot: %s", e)


def run_mock():
    # Provide mocked metrics to avoid external API dependency
    state = {
        "agent_id": "123",
        "date": "2024-01-01",
        "raw_metrics": {
            "performance": {
                "mtd_sales_value": 30.0,
                "active_days_mtd": 10,
                "mtd_order_count": 20,
                "last12m_order_count": 200
            },
            "dc_activity": {
                "unique_dcs_visited": 5,
                "total_dcs": 20,
                "check_ins_count": 10,
                "expected_check_ins": 20
            },
            "outstanding": {
                "outstanding_amount": 50000
            },
            "onboarding": {
                "new_retailers_mtd": 2,
                "new_retailers_last_month": 4,
                "new_retailers_last12m": 20
            }
        },
        "bo_results": {},
        "final_priority_order": []
    }

    # Simulate parallel partial updates by invoking each BO node and merging partials
    def _merge(state, partial):
        if not partial:
            return state
        for k, v in partial.items():
            if k == "bo_results":
                state.setdefault("bo_results", {}).update(v)
            else:
                state[k] = v
        return state

    # simple tracing log for each node
    for fn in (b01, b02, b03, b04, b05):
        logger.info("Invoking node %s", fn.__name__)
        partial = fn(state)
        logger.info("Node %s returned: %s", fn.__name__, bool(partial))
        state = _merge(state, partial)

    # merge sync node
    partial = merge_bo_results(state)
    state = _merge(state, partial)

    state = prioritize(state)

    print("BO Results:")
    for bo, data in state.get("bo_results", {}).items():
        print(f"  {bo}: ratio={data.get('ratio'):.4f}, grade={data.get('grade')}")

    print("Final priority order:", state.get("final_priority_order"))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run the mock workflow with optional persistence and tracing")
    p.add_argument("--thread-id", default=os.environ.get("THREAD_ID", "session_1"), help="thread/session id to tag persisted state")
    p.add_argument("--persist-path", default=None, help="optional path to save state snapshot (JSON)")
    args = p.parse_args()

    logger.info("LangSmith API key present: %s", bool(os.environ.get("LANGSMITH_API_KEY")))
    run_mock()
    # write out a snapshot for persistence/troubleshooting
    # Note: run_mock updates local variable `state` only inside function; call run_mock and then save
    # To get the final state we re-run but return state (quick and simple change)
    final_state = None
    def run_and_return():
        # replicate run_mock but return final state
        state = {
            "agent_id": "123",
            "date": "2024-01-01",
            "raw_metrics": {
                "performance": {"mtd_sales_value": 30.0, "active_days_mtd": 10, "mtd_order_count": 20, "last12m_order_count": 200},
                "dc_activity": {"unique_dcs_visited": 5, "total_dcs": 20, "check_ins_count": 10, "expected_check_ins": 20},
                "outstanding": {"outstanding_amount": 50000},
                "onboarding": {"new_retailers_mtd": 2, "new_retailers_last_month": 4, "new_retailers_last12m": 20}
            },
            "bo_results": {},
            "final_priority_order": []
        }
        def _merge(state, partial):
            if not partial:
                return state
            for k, v in partial.items():
                if k == "bo_results":
                    state.setdefault("bo_results", {}).update(v)
                else:
                    state[k] = v
            return state
        for fn in (b01, b02, b03, b04, b05):
            partial = fn(state)
            state = _merge(state, partial)
        state = _merge(state, merge_bo_results(state))
        state = prioritize(state)
        return state

    final_state = run_and_return()
    _save_state(final_state, args.thread_id, args.persist_path)

if __name__ == "__main__":
    run_mock()
