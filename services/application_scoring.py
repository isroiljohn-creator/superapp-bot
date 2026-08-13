"""Application (ariza) scoring — independent of User.lead_score/lead_segment.

First-draft rubric — the owner should tune weights/thresholds once real
conversion data comes in. Tiers match the funnel's 4-level table:
0-20 cold, 20-50 warm, 50-80 hot, 80+ ready.
"""

# question_key -> {answer_value: points}
SCORE_MAP = {
    "budget": {"ready": 30, "partial": 15, "none": 0},
    "timeline": {"today": 25, "this_week": 15, "later": 5},
    "experience": {"beginner": 10, "some": 15, "experienced": 20},
    "motivation": {"curious": 5, "serious": 15, "career": 25},
}

TIER_THRESHOLDS = [
    (80, "ready"),
    (50, "hot"),
    (20, "warm"),
    (0, "cold"),
]


def score_answers(answers: dict) -> int:
    """Sum points for each answered question; unanswered/unknown values score 0."""
    total = 0
    for question, value in answers.items():
        total += SCORE_MAP.get(question, {}).get(value, 0)
    return total


def tier_for_score(score: int) -> str:
    for threshold, tier in TIER_THRESHOLDS:
        if score >= threshold:
            return tier
    return "cold"


class ApplicationScoringService:
    """Thin wrapper mirroring services/lead_scoring.py's LeadScoringService shape."""

    def score(self, answers: dict) -> tuple[int, str]:
        total = score_answers(answers)
        return total, tier_for_score(total)
