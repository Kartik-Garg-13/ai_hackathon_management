from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MIN_RELEVANCE = 0.08


@dataclass
class MentorProfile:
    mentor_id: int
    text: str


def rank_mentors_by_relevance(query_text: str, mentors: list[MentorProfile]) -> list[tuple[int, float]]:
    usable = [m for m in mentors if m.text and m.text.strip()]
    if not query_text.strip() or len(usable) == 0:
        return []

    corpus = [query_text] + [m.text for m in usable]
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        vectors = vectorizer.fit_transform(corpus)
    except ValueError:
        return []

    query_vector = vectors[0]
    mentor_vectors = vectors[1:]
    scores = cosine_similarity(query_vector, mentor_vectors)[0]

    ranked = sorted(
        ((usable[i].mentor_id, round(float(scores[i]), 3)) for i in range(len(usable))),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return [pair for pair in ranked if pair[1] >= MIN_RELEVANCE]
