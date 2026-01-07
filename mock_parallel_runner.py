import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
import logging
import os
from dotenv import load_dotenv

from nodes.b01 import b01
from nodes.b02 import b02
from nodes.b03 import b03
from nodes.b04 import b04
from nodes.b05 import b05
from nodes.merge_bo_results import merge_bo_results
from nodes.resolve_priority import prioritize

# load env for optional tracing integrations (e.g. LANGCHAIN_API_KEY or LANGSMITH_API_KEY)
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mock-parallel-runner")

# Note: This mock workflow does NOT use LangGraph, so it won't generate LangSmith traces.
# Use main.py for LangGraph-based workflows that will generate traces.


def _merge_into(state: dict, partial: dict, lock: threading.Lock):
    if not partial:
        return
    with lock:
        for k, v in partial.items():
            if k == "bo_results":
                state.setdefault("bo_results", {}).update(v)
            else:
                state[k] = v


def _save_state(state: dict, thread_id: str, path: str = None):
    if path is None:
        path = f"mock_parallel_state_{thread_id}.json"
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
        logger.info("Saved parallel-run state to %s", path)
    except Exception as e:
        logger.warning("Failed to save parallel-run state: %s", e)


def run_parallel_mock(thread_id: str = "session_1", persist_path: str = None):
    state = {
        "agent_id": "123",
        "date": "2024-01-01",
        "raw_metrics": {
            "performance": {
                "mtd_sales_value": 30.0,
                "active_days_mtd": 10,
                "mtd_order_count": 20,
                "last12m_order_count": 200,
                "last_month_sales": 40,
                "unique_transacting_dcs_mtd": 5,
                "last_month_active_dcs": 6,
                "pl_sales_last_12m": 240,
            },
            "dc_activity": {
                "unique_dcs_visited": 5,
                "total_dcs": 20,
                "check_ins_count": 10,
                "expected_check_ins": 20,
                "last_month_unique_dcs": 8,
                "last_month_checkins": 40,
            },
            "outstanding": {
                "outstanding_amount": 50000,
                "last_month_ar": 80000,
            },
            "onboarding": {
                "new_retailers_mtd": 2,
                "new_retailers_last_month": 4,
                "new_retailers_last12m": 20,
            },
        },
        "bo_results": {},
        "final_priority_order": []
    }

    lock = threading.Lock()
    funcs = [b01, b02, b03, b04, b05]

    # Check for LangSmith/LangChain API key (LangSmith uses LANGCHAIN_API_KEY)
    api_key = os.environ.get("LANGCHAIN_API_KEY") or os.environ.get("LANGSMITH_API_KEY")
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1", "yes")
    logger.info("LangSmith/LangChain API key present: %s", bool(api_key))
    logger.info("Note: Mock workflows don't use LangGraph, so they won't generate LangSmith traces.")
    logger.info("Use 'python main.py' for workflows that generate LangSmith traces.")

    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(fn, state): fn.__name__ for fn in funcs}
        for fut in as_completed(futures):
            partial = None
            try:
                partial = fut.result()
            except Exception as e:
                logger.exception("Node %s raised: %s", futures[fut], e)
            if partial:
                logger.info("Merging partial from %s", futures[fut])
                _merge_into(state, partial, lock)

    # merge sync node (no-op here but kept for parity)
    m = merge_bo_results(state)
    _merge_into(state, m, lock)

    # finalize priorities
    state = prioritize(state)

    logger.info("BO Results:")
    for bo, data in state.get("bo_results", {}).items():
        logger.info("  %s: ratio=%.4f, grade=%s", bo, data.get("ratio", 0.0), data.get("grade"))
    logger.info("Final priority order: %s", state.get("final_priority_order"))

    # persist snapshot
    _save_state(state, thread_id, persist_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run mock parallel workflow with optional persistence/tracing")
    p.add_argument("--thread-id", default=os.environ.get("THREAD_ID", "session_1"), help="thread/session id to tag persisted state")
    p.add_argument("--persist-path", default=None, help="optional path to save state snapshot (JSON)")
    args = p.parse_args()
    run_parallel_mock(args.thread_id, args.persist_path)
