from dataclasses import dataclass

import numpy as np

Z_LENIENT_THRESHOLD = 1.2
Z_HARSH_THRESHOLD = -1.2
MIN_SCORES_FOR_BIAS = 3


@dataclass
class ReviewerBiasResult:
    reviewer_id: int
    num_scores: int
    mean_score: float
    z_score: float
    bias_risk_level: str
    bias_confidence: float
    confidence_label: str
    flags: list[str]
    summary: str


def compute_population_stats(all_scores: list[float]) -> tuple[float, float]:
    if not all_scores:
        return 0.0, 1.0
    arr = np.array(all_scores, dtype=float)
    mean = float(arr.mean())
    std = float(arr.std())
    return mean, std if std > 1e-6 else 1.0


def iqr_outliers(scores: list[float]) -> list[int]:
    if len(scores) < 4:
        return []
    arr = np.array(scores, dtype=float)
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [i for i, v in enumerate(arr) if v < lower or v > upper]


def _confidence_label(confidence: float) -> str:
    if confidence >= 75:
        return "Very High"
    if confidence >= 50:
        return "High"
    if confidence >= 25:
        return "Moderate"
    return "Low"


def _build_summary(
    risk_level: str,
    direction: str | None,
    mean_score: float,
    population_mean: float,
    outlier_count: int,
    n: int,
) -> str:
    if risk_level == "Insufficient Data":
        return f"Only {n} score(s) submitted so far — not enough data yet to judge fairness."

    if risk_level == "Low":
        return (
            f"Scoring looks consistent with other reviewers (average {mean_score:.0f} "
            f"vs. typical {population_mean:.0f}). No fairness concerns."
        )

    direction_text = (
        f"scores noticeably {'lower' if direction == 'harsh' else 'higher'} than other reviewers "
        f"(average {mean_score:.0f} vs. typical {population_mean:.0f})"
        if direction
        else f"has inconsistent scoring patterns across teams ({outlier_count} unusual score(s))"
    )
    severity = "Strong evidence" if risk_level == "High" else "Some evidence"
    return f"{severity} this reviewer {direction_text}. Recommend a second opinion on their reviews."


def analyze_reviewer_bias(
    reviewer_id: int,
    reviewer_scores: list[float],
    population_mean: float,
    population_std: float,
) -> ReviewerBiasResult:
    n = len(reviewer_scores)
    mean_score = float(np.mean(reviewer_scores)) if n else 0.0
    z = (mean_score - population_mean) / population_std if n else 0.0

    flags: list[str] = []
    if n < MIN_SCORES_FOR_BIAS:
        return ReviewerBiasResult(
            reviewer_id=reviewer_id,
            num_scores=n,
            mean_score=round(mean_score, 2),
            z_score=round(z, 2),
            bias_risk_level="Insufficient Data",
            bias_confidence=0.0,
            confidence_label="Low",
            flags=["Fewer than 3 scores submitted"],
            summary=_build_summary("Insufficient Data", None, mean_score, population_mean, 0, n),
        )

    direction = None
    if z >= Z_LENIENT_THRESHOLD:
        direction = "lenient"
        flags.append(f"Consistently Lenient (z={z:.2f})")
    elif z <= Z_HARSH_THRESHOLD:
        direction = "harsh"
        flags.append(f"Consistently Harsh (z={z:.2f})")

    # within-batch outliers measure inconsistency, not population-relative bias — kept out of risk_level
    outlier_idxs = iqr_outliers(reviewer_scores)
    if outlier_idxs:
        flags.append(f"{len(outlier_idxs)} outlier score(s) within own batch")

    abs_z = abs(z)
    if abs_z >= 2.5:
        risk_level = "High"
    elif abs_z >= Z_LENIENT_THRESHOLD:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    sample_weight = min(1.0, n / 10)
    deviation_weight = min(1.0, abs_z / 3)
    confidence = round(100 * (0.5 * sample_weight + 0.5 * deviation_weight), 2)

    if not flags:
        flags.append("No significant bias detected")

    return ReviewerBiasResult(
        reviewer_id=reviewer_id,
        num_scores=n,
        mean_score=round(mean_score, 2),
        z_score=round(z, 2),
        bias_risk_level=risk_level,
        bias_confidence=confidence,
        confidence_label=_confidence_label(confidence),
        flags=flags,
        summary=_build_summary(risk_level, direction, mean_score, population_mean, len(outlier_idxs), n),
    )


def normalize_score(
    raw_score: float,
    reviewer_mean: float,
    reviewer_std: float,
    population_mean: float,
    population_std: float,
) -> float:
    std = reviewer_std if reviewer_std > 1e-6 else 1.0
    normalized = population_mean + (raw_score - reviewer_mean) / std * population_std
    return round(max(0.0, min(100.0, normalized)), 2)


def explain_normalization(reviewer_mean: float, population_mean: float) -> str:
    diff = reviewer_mean - population_mean
    if abs(diff) < 3:
        return "No adjustment needed — this judge's scoring is close to the typical average."
    direction = "above" if diff > 0 else "below"
    adjustment = "down" if diff > 0 else "up"
    return f"Adjusted {adjustment} — this judge tends to score {abs(diff):.0f}pts {direction} average."


def fairness_report(scores_by_reviewer: dict[int, list[float]]) -> list[ReviewerBiasResult]:
    results = []
    for reviewer_id, scores in scores_by_reviewer.items():
        other_scores = [
            s for rid, rscores in scores_by_reviewer.items() if rid != reviewer_id for s in rscores
        ]
        pop_mean, pop_std = compute_population_stats(other_scores or scores)
        results.append(analyze_reviewer_bias(reviewer_id, scores, pop_mean, pop_std))
    return results
