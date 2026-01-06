import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from nodes.b01 import b01
from nodes.b02 import b02
from nodes.b03 import b03
from nodes.b04 import b04
from nodes.b05 import b05
from nodes.merge_bo_results import merge_bo_results
from nodes.resolve_priority import prioritize


def _merge_into(state: dict, partial: dict, lock: threading.Lock):
    if not partial:
        return
    with lock:
        for k, v in partial.items():
            if k == "bo_results":
                state.setdefault("bo_results", {}).update(v)
            else:
                state[k] = v


def run_parallel_mock():
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

    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(fn, state): fn.__name__ for fn in funcs}
        for fut in as_completed(futures):
            partial = None
            try:
                partial = fut.result()
            except Exception as e:
                print(f"Node {futures[fut]} raised: {e}")
            if partial:
                _merge_into(state, partial, lock)

    # merge sync node (no-op here but kept for parity)
    m = merge_bo_results(state)
    _merge_into(state, m, lock)

    # finalize priorities
    state = prioritize(state)

    print("BO Results:")
    for bo, data in state.get("bo_results", {}).items():
        print(f"  {bo}: ratio={data.get('ratio'):.4f}, grade={data.get('grade')}")
    print("Final priority order:", state.get("final_priority_order"))


if __name__ == "__main__":
    run_parallel_mock()
