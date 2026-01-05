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
    state = b01(state)
    state = b02(state)
    state = b03(state)
    state = b04(state)
    state = b05(state)
    state = merge_bo_results(state)
    return state