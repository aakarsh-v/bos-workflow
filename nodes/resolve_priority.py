import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState
from utils.config import get_config


def _assign_grade_from_thresholds(ratio: float, thresholds: dict) -> str:
    # thresholds: {"A": 1.0, "B": 0.5, ...}
    # Choose the highest grade whose threshold <= ratio
    # Sort grades by threshold descending so A, B, C, D
    for grade, th in sorted(thresholds.items(), key=lambda x: -x[1]):
        if ratio >= th:
            return grade
    return "D"


def prioritize(state: AgentState):
    results = state.get("bo_results", {})
    cfg = get_config() or {}

    # Load grade thresholds from config, fallback to hard-coded
    grade_thresholds = cfg.get("grade_thresholds", {"A": 1.0, "B": 0.5, "C": 0.25, "D": 0.0})

    # 1. Assign Grades based on thresholds (initial grades)
    initial_grades = {}
    for bo, data in results.items():
        ratio = data.get("ratio", 0)
        # Get thresholds from BO config if available, otherwise use global
        bo_conf = next((b for b in cfg.get("business_objectives", []) if b["bo_code"] == bo), {})
        bo_thresholds = bo_conf.get("grading", {}).get("thresholds", grade_thresholds)
        g = _assign_grade_from_thresholds(ratio, bo_thresholds)
        data["grade"] = g
        initial_grades[bo] = g

    # 2. Apply Conditional Priority Rules from config
    priority_rules = cfg.get("priority_rules", {})
    for rule in priority_rules.get("conditional_rules", []):
        cond = rule.get("if", {})
        then = rule.get("then", {})
        cond_bo = cond.get("bo") or cond.get("bo_code")
        cond_grade = cond.get("grade")
        if cond_bo and results.get(cond_bo, {}).get("grade") == cond_grade:
            # support set_grade action or CAP_GRADE action
            set_grade = then.get("set_grade")
            if set_grade:
                tgt = set_grade.get("bo")
                g = set_grade.get("grade")
                if tgt and tgt in results:
                    results[tgt]["grade"] = g
            # support CAP_GRADE action from config
            elif then.get("action") == "CAP_GRADE":
                tgt = then.get("target_bo")
                g = then.get("cap_to")
                if tgt and tgt in results and g:
                    results[tgt]["grade"] = g

    # 3. Determine default order and grade priority mapping
    default_order = priority_rules.get("default_priority_order", cfg.get("default_order", ["BO1", "BO2", "BO4", "BO3", "BO5"]))

    # Build grade ordering: lower grades first (D, C, B, A) for prioritization
    # We derive order by sorting thresholds ascending
    sorted_grades = [g for g, _ in sorted(grade_thresholds.items(), key=lambda x: x[1])]
    grade_priority = {g: i for i, g in enumerate(sorted_grades)}

    # Sort: First by grade priority (lower threshold = higher priority), then by default order
    sorted_bos = sorted(
        results.keys(),
        key=lambda bo: (
            grade_priority.get(results[bo].get("grade", "D"), 0),
            default_order.index(bo) if bo in default_order else 999
        )
    )

    # 4. Apply explicit priority override if configured
    # Check for priority_override in conditional rules first
    explicit = None
    for rule in priority_rules.get("conditional_rules", []):
        then = rule.get("then", {})
        if then.get("priority_override"):
            explicit = then.get("priority_override")
            break
    
    # Fallback to priority_overrides section if exists
    po = cfg.get("priority_overrides", {})
    if explicit is None:
        explicit = po.get("explicit_order", []) or []
    
    apply_only_when_all_D = False
    # Check if we should apply only when all D
    for rule in priority_rules.get("conditional_rules", []):
        cond = rule.get("if", {})
        if cond.get("all_bos_grade") == "D":
            apply_only_when_all_D = True
            break

    def _all_grades_are_D(res):
        return all((res.get(bo, {}).get("grade") == "D") for bo in res.keys())

    # Decide whether to evaluate 'all D' on initial grades or after conditional rules
    evaluate_on_initial = po.get("evaluate_on_initial_grades", True)

    should_apply_explicit = False
    if explicit:
        if apply_only_when_all_D:
            if evaluate_on_initial:
                # check initial grades captured earlier
                should_apply_explicit = all(g == "D" for g in initial_grades.values())
            else:
                should_apply_explicit = _all_grades_are_D(results)
        else:
            should_apply_explicit = True

    if should_apply_explicit:
        # Keep only BOs that exist, preserve configured order
        final_order = [bo for bo in explicit if bo in results]
        # append any missing BOs at end preserving computed order
        final_order += [bo for bo in sorted_bos if bo not in final_order]
    else:
        final_order = sorted_bos

    state["final_priority_order"] = final_order
    return state