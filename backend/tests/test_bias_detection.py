import random

from app.services.bias_detection import explain_normalization, fairness_report, iqr_outliers, normalize_score


def test_harsh_reviewer_flagged_high_risk():
    scores_by_reviewer = {
        1: [70, 72, 68, 75, 71, 73, 69, 74],
        2: [71, 70, 73, 69, 72, 74, 70, 71],
        3: [30, 28, 32, 25, 29, 31, 27, 26],
    }
    report = {r.reviewer_id: r for r in fairness_report(scores_by_reviewer)}
    assert report[3].bias_risk_level == "High"
    assert report[3].z_score < -1.5
    assert any("Harsh" in f for f in report[3].flags)


def test_consistent_reviewer_flagged_low_risk():
    scores_by_reviewer = {
        1: [70, 72, 68, 75, 71, 73, 69, 74],
        2: [71, 70, 73, 69, 72, 74, 70, 71],
    }
    report = {r.reviewer_id: r for r in fairness_report(scores_by_reviewer)}
    assert report[1].bias_risk_level == "Low"
    assert report[2].bias_risk_level == "Low"


def test_insufficient_data_flagged_when_few_scores():
    scores_by_reviewer = {1: [70, 72]}
    report = fairness_report(scores_by_reviewer)
    assert report[0].bias_risk_level == "Insufficient Data"


def test_iqr_outliers_detects_extreme_value():
    scores = [70, 71, 69, 72, 70, 5]
    outliers = iqr_outliers(scores)
    assert 5 in outliers


def test_normalize_score_pulls_lenient_and_harsh_reviewers_closer():
    population_mean, population_std = 62.0, 10.0
    lenient_normalized = normalize_score(71.1, reviewer_mean=73.0, reviewer_std=8.0,
                                          population_mean=population_mean, population_std=population_std)
    harsh_normalized = normalize_score(54.2, reviewer_mean=52.0, reviewer_std=6.0,
                                        population_mean=population_mean, population_std=population_std)
    raw_gap = 71.1 - 54.2
    normalized_gap = abs(lenient_normalized - harsh_normalized)
    assert normalized_gap < raw_gap


def test_explain_normalization_describes_direction():
    assert "below average" in explain_normalization(reviewer_mean=50, population_mean=65)
    assert "above average" in explain_normalization(reviewer_mean=80, population_mean=65)
    assert "No adjustment" in explain_normalization(reviewer_mean=64, population_mean=65)


def test_bias_detection_accuracy_on_a_realistic_reviewer_panel():
    rng = random.Random(7)
    scores_by_reviewer: dict[int, list[float]] = {}
    ground_truth_biased: dict[int, bool] = {}

    reviewer_id = 0
    for _ in range(14):  # fair reviewers
        reviewer_id += 1
        scores_by_reviewer[reviewer_id] = [max(0, min(100, rng.gauss(70, 8))) for _ in range(10)]
        ground_truth_biased[reviewer_id] = False
    for _ in range(4):  # harsh reviewers
        reviewer_id += 1
        scores_by_reviewer[reviewer_id] = [max(0, min(100, rng.gauss(55, 6))) for _ in range(10)]
        ground_truth_biased[reviewer_id] = True
    for _ in range(2):  # lenient reviewers
        reviewer_id += 1
        scores_by_reviewer[reviewer_id] = [max(0, min(100, rng.gauss(85, 6))) for _ in range(10)]
        ground_truth_biased[reviewer_id] = True

    report = {r.reviewer_id: r for r in fairness_report(scores_by_reviewer)}
    flagged = {rid: r.bias_risk_level in ("Medium", "High") for rid, r in report.items()}

    true_positives = sum(1 for rid in ground_truth_biased if ground_truth_biased[rid] and flagged[rid])
    false_negatives = sum(1 for rid in ground_truth_biased if ground_truth_biased[rid] and not flagged[rid])
    false_positives = sum(1 for rid in ground_truth_biased if not ground_truth_biased[rid] and flagged[rid])
    true_negatives = sum(1 for rid in ground_truth_biased if not ground_truth_biased[rid] and not flagged[rid])

    accuracy = (true_positives + true_negatives) / len(ground_truth_biased)
    recall = true_positives / (true_positives + false_negatives)
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 1.0

    assert accuracy >= 0.9, f"accuracy {accuracy:.2f} on a 20-reviewer panel (6 biased, 14 fair)"
    assert recall >= 0.9, f"recall {recall:.2f} — biased reviewers must actually get caught"
    assert precision >= 0.9, f"precision {precision:.2f} — fair reviewers must not be falsely flagged"
