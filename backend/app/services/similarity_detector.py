from dataclasses import dataclass

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DUPLICATE_THRESHOLD = 0.55


@dataclass
class TeamProject:
    team_id: int
    team_name: str
    text: str


@dataclass
class SimilarPair:
    team_a_id: int
    team_a_name: str
    team_b_id: int
    team_b_name: str
    similarity: float


@dataclass
class ProjectCategory:
    label: str
    team_count: int
    team_ids: list[int]


def find_similar_projects(projects: list[TeamProject], threshold: float = DUPLICATE_THRESHOLD) -> list[SimilarPair]:
    usable = [p for p in projects if p.text and p.text.strip()]
    if len(usable) < 2:
        return []

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([p.text for p in usable])
    sim_matrix = cosine_similarity(vectors)

    pairs = []
    for i in range(len(usable)):
        for j in range(i + 1, len(usable)):
            score = float(sim_matrix[i][j])
            if score >= threshold:
                pairs.append(SimilarPair(
                    team_a_id=usable[i].team_id, team_a_name=usable[i].team_name,
                    team_b_id=usable[j].team_id, team_b_name=usable[j].team_name,
                    similarity=round(score, 3),
                ))
    pairs.sort(key=lambda p: p.similarity, reverse=True)
    return pairs


def categorize_projects(projects: list[TeamProject], max_clusters: int = 6) -> list[ProjectCategory]:
    usable = [p for p in projects if p.text and p.text.strip()]
    if not usable:
        return []
    if len(usable) < 3:
        return [ProjectCategory(label="General", team_count=len(usable), team_ids=[p.team_id for p in usable])]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
    vectors = vectorizer.fit_transform([p.text for p in usable])
    terms = vectorizer.get_feature_names_out()

    k = max(2, min(max_clusters, len(usable) // 2))
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(vectors)

    categories: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        categories.setdefault(int(label), []).append(idx)

    results = []
    for cluster_id, indices in categories.items():
        center = model.cluster_centers_[cluster_id]
        top_term_idx = center.argsort()[::-1][:3]
        label = " / ".join(terms[i].title() for i in top_term_idx if center[i] > 0) or "General"
        results.append(ProjectCategory(
            label=label,
            team_count=len(indices),
            team_ids=[usable[i].team_id for i in indices],
        ))
    results.sort(key=lambda c: c.team_count, reverse=True)
    return results
