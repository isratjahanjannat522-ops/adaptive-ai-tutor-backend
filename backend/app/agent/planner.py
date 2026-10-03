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
    Deterministic, explainable adaptive policy for the thesis.
    Returns one of:
      - verify_and_review
      - review
      - practice
      - teach
      - advance
    """ 

    def choose(self, state: StudentState) -> str:
        # High confidence but low demonstrated mastery → verification needed
        if state.confidence_gap >= 20:
            return "verify_and_review"

        # Low mastery → review fundamentals
        if state.mastery < 50:
            return "review"

        # Weak recent performance → practice
        if state.recent_score is not None and state.recent_score < 70:
            return "practice"

        # Strong mastery + strong recent score → advance
        if (
            state.mastery >= 85
            and state.recent_score is not None
            and state.recent_score >= 85
        ):
            return "advance"

        # Default: teach at standard level
        return "teach"


def action_to_difficulty(action: str) -> str:
    mapping = {
        "review": "easy",
        "practice": "moderate",
        "teach": "standard",
        "advance": "challenging",
        "verify_and_review": "easy_with_verification",
    }
    return mapping.get(action, "standard")