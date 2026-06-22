from dataclasses import dataclass


@dataclass
class MentorLeaderboardResult:
    mentor_id: int
    response_count: int
    average_rating: float | None
    summary: str


def _build_summary(response_count: int, average_rating: float | None) -> str:
    if response_count == 0:
        return "No queries answered yet."
    if average_rating is None:
        return f"Answered {response_count} quer{'y' if response_count == 1 else 'ies'} — no ratings yet."
    quality = "Highly rated" if average_rating >= 4.5 else "Well rated" if average_rating >= 3.5 else "Mixed feedback"
    return f"{quality} — {response_count} quer{'y' if response_count == 1 else 'ies'} answered, average rating {average_rating:.1f}/5."


def build_leaderboard(queries_by_mentor: dict[int, list[dict]]) -> list[MentorLeaderboardResult]:
    results = []
    for mentor_id, queries in queries_by_mentor.items():
        answered = [q for q in queries if q.get("status") == "answered"]
        ratings = [q["rating"] for q in answered if q.get("rating") is not None]
        average_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
        results.append(MentorLeaderboardResult(
            mentor_id=mentor_id,
            response_count=len(answered),
            average_rating=average_rating,
            summary=_build_summary(len(answered), average_rating),
        ))
    results.sort(key=lambda r: (r.average_rating or 0, r.response_count), reverse=True)
    return results
