import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState


def merge_bo_results(state: AgentState):
    # Join point / synchronization node. No-op partial return so orchestration
    # can merge bo_results from parallel nodes without overwriting.
    return {}
