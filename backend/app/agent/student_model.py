from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TopicEvidence:
    score: float
    confidence: Optional[float]
    time_spent_seconds: int


class StudentModelUpdater:
    """
    Explainable exponential-moving-average student model.
    Suitable for a thesis prototype.
    """

    MASTERY_ALPHA = 0.40
    CONFIDENCE_ALPHA = 0.40
    SPEED_ALPHA = 0.30

    def update_mastery(self, previous: float, new_score: float, is_first: bool) -> float:
        if is_first:
            return new_score
        return self.MASTERY_ALPHA * new_score + (1 - self.MASTERY_ALPHA) * previous

    def update_confidence(
        self, previous: float, reported: Optional[float], is_first: bool
    ) -> float:
        if reported is None:
            return previous
        if is_first:
            return reported
        return self.CONFIDENCE_ALPHA * reported + (1 - self.CONFIDENCE_ALPHA) * previous

    def update_learning_speed(
        self,
        previous_speed: float,
        mastery_gain: float,
        time_spent_seconds: int,
    ) -> float:
        """
        Simple indicator: more gain per unit time → higher speed.
        Clamped for stability.
        """
        if time_spent_seconds <= 0:
            return previous_speed

        # Normalize: expect ~5 points gain per minute as baseline = 1.0
        minutes = max(time_spent_seconds / 60.0, 0.1)
        raw = mastery_gain / minutes
        # Map roughly to 0.5 – 2.0 range
        indicator = max(0.5, min(2.0, 1.0 + (raw / 10.0)))

        return self.SPEED_ALPHA * indicator + (1 - self.SPEED_ALPHA) * previous_speed