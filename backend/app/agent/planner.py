from dataclasses import dataclass
from typing import Optional


@dataclass
class StudentState:
    mastery: float = 0.0
    confidence: float = 0.0
    learning_speed: float = 1.0
    recent_score: Optional[float] = None
    confidence_gap: float = 0.0
    course_progress: float = 0.0


class AdaptivePlanner:
    """
    Deterministic, explainable adaptive policy.
    Returns only one of:
      - practice
      - teach
      - advance
    """

    def choose(self, state: StudentState) -> str:
        # 90+ recent score → unlock advance (next chapter option)
        if state.recent_score is not None and state.recent_score >= 90:
            return "advance"

        # Low mastery or weak recent performance → practice
        if state.mastery < 55 or (
            state.recent_score is not None and state.recent_score < 70
        ):
            return "practice"

        # Strong but not yet 90 → still allow advance if mastery is high
        if state.mastery >= 85 and (
            state.recent_score is None or state.recent_score >= 80
        ):
            return "advance"

        # Default
        return "teach"


def action_to_difficulty(action: str) -> str:
    mapping = {
        "practice": "moderate",
        "teach": "standard",
        "advance": "challenging",
    }
    return mapping.get(action, "standard")