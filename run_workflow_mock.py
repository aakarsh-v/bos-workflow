from nodes.resolve_priority import prioritize
from nodes.b01 import b01
from nodes.b02 import b02
from nodes.b03 import b03
from nodes.b04 import b04
from nodes.b05 import b05
from nodes.merge_bo_results import merge_bo_results


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

    for fn in (b01, b02, b03, b04, b05):
        partial = fn(state)
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
    run_mock()
