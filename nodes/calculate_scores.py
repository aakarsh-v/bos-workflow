import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState

# Backwards-compatible wrapper: call individual BO nodes so older callers still work
from nodes.b01 import b01
from nodes.b02 import b02
from nodes.b03 import b03
from nodes.b04 import b04
from nodes.b05 import b05
from nodes.merge_bo_results import merge_bo_results


def calculate_scores(state: AgentState):
    # Each BO node now returns a partial dict. Merge them into the main state
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

    # merge node is a sync point; if it returns partials merge them as well
    partial = merge_bo_results(state)
    state = _merge(state, partial)
    return state