from app.services.mentor_matcher import MentorProfile, rank_mentors_by_relevance


def test_ranks_mentor_with_matching_expertise_first():
    mentors = [
        MentorProfile(mentor_id=1, text="React Frontend JavaScript UI design"),
        MentorProfile(mentor_id=2, text="Machine Learning Python TensorFlow NLP"),
    ]
    ranked = rank_mentors_by_relevance("Need help with React state management", mentors)
    assert ranked
    assert ranked[0][0] == 1


def test_returns_empty_when_no_relevant_mentor():
    mentors = [MentorProfile(mentor_id=1, text="Blockchain Solidity smart contracts")]
    ranked = rank_mentors_by_relevance("Need help with database indexing performance", mentors)
    assert ranked == [] or ranked[0][1] < 0.3


def test_handles_no_mentors():
    assert rank_mentors_by_relevance("Need help with React", []) == []


def test_handles_blank_query():
    mentors = [MentorProfile(mentor_id=1, text="React expert")]
    assert rank_mentors_by_relevance("", mentors) == []
