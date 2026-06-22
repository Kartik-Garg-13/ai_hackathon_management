from app.services.mentor_leaderboard import build_leaderboard


def test_mentor_with_high_ratings_ranks_first():
    queries_by_mentor = {
        1: [{"status": "answered", "rating": 5}, {"status": "answered", "rating": 4}],
        2: [{"status": "answered", "rating": 2}, {"status": "answered", "rating": 3}],
    }
    results = {r.mentor_id: r for r in build_leaderboard(queries_by_mentor)}
    assert results[1].average_rating > results[2].average_rating
    ranked = build_leaderboard(queries_by_mentor)
    assert ranked[0].mentor_id == 1


def test_mentor_with_no_answers_has_no_rating():
    queries_by_mentor = {1: [{"status": "open", "rating": None}]}
    results = build_leaderboard(queries_by_mentor)
    assert results[0].response_count == 0
    assert results[0].average_rating is None


def test_unrated_responses_still_count_toward_response_count():
    queries_by_mentor = {1: [{"status": "answered", "rating": None}, {"status": "answered", "rating": None}]}
    results = build_leaderboard(queries_by_mentor)
    assert results[0].response_count == 2
    assert results[0].average_rating is None
