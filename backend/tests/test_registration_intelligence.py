from app.services import registration_intelligence as ri


def test_analyze_adds_expected_columns(sample_df):
    out = ri.analyze(sample_df)
    for col in ["final_trust_score", "final_risk_level", "confidence_score", "explanation", "predicted_label"]:
        assert col in out.columns
    assert len(out) == len(sample_df)


def test_fake_email_is_flagged_high_risk(sample_df):
    out = ri.analyze(sample_df)
    fake_rows = out[out["email"].str.contains("testmail.xyz")]
    assert (fake_rows["final_risk_level"] == "High Risk").all()
    assert (fake_rows["email_trust_score"] == 0).all()


def test_genuine_well_formed_registration_scores_higher_than_fake(sample_df):
    out = ri.analyze(sample_df)
    genuine_trust = out[out["email"] == "amangupta1@gmail.com"]["final_trust_score"].iloc[0]
    fake_trust = out[out["email"] == "fakeuser4@testmail.xyz"]["final_trust_score"].iloc[0]
    assert genuine_trust > fake_trust


def test_duplicate_email_name_pair_detected(sample_df):
    out = ri.analyze(sample_df)
    dup_rows = out[out["email"] == "fakeuser4@testmail.xyz"]
    assert len(dup_rows) == 2
    assert all(any(r.startswith("Duplicate of") for r in reasons) for reasons in dup_rows["reasons"])


def test_with_timestamps_only_the_later_duplicate_is_penalized(sample_df):
    import pandas as pd
    df = sample_df.copy()
    df["created_at"] = [
        "2026-01-01T10:00:00", "2026-01-01T10:01:00", "2026-01-01T10:02:00",
        "2026-01-01T09:00:00", "2026-01-01T09:05:00",
    ]
    out = ri.analyze(df)
    dup_rows = out[out["email"] == "fakeuser4@testmail.xyz"].sort_values("created_at")
    earliest, later = dup_rows.iloc[0], dup_rows.iloc[1]
    assert not any(r.startswith("Duplicate of") for r in earliest["reasons"])
    assert any(r.startswith("Duplicate of") for r in later["reasons"])


def test_duplicate_email_across_different_names_only_penalizes_later_one_with_timestamps():
    import pandas as pd
    df = pd.DataFrame([
        {"id": "T1_001", "name": "Alice First", "email": "shared@gmail.com", "college": "X", "skills": "Python",
         "project_idea": "App A", "team_name": "TeamA", "phone_number": "+910000000001",
         "created_at": "2026-01-01T09:00:00"},
        {"id": "T2_001", "name": "Bob Second", "email": "shared@gmail.com", "college": "Y", "skills": "React",
         "project_idea": "App B", "team_name": "TeamB", "phone_number": "+910000000002",
         "created_at": "2026-01-01T10:00:00"},
    ])
    out = ri.analyze(df)
    earlier = out[out["name"] == "Alice First"].iloc[0]
    later = out[out["name"] == "Bob Second"].iloc[0]
    assert "Duplicate Email" not in earlier["reasons"]
    assert "Duplicate Email" in later["reasons"]


def test_evaluate_returns_metrics_when_ground_truth_present(sample_df):
    out = ri.analyze(sample_df)
    metrics = ri.evaluate(out)
    assert metrics is not None
    assert 0 <= metrics["accuracy"] <= 1


def test_evaluate_returns_none_without_ground_truth(sample_df):
    df = sample_df.drop(columns=["ground_truth_label"])
    out = ri.analyze(df)
    assert ri.evaluate(out) is None


def test_email_intelligence_suggests_typo_correction():
    result = ri.email_intelligence("someone@gmial.com")
    assert "Typo Domain" in result["flags"]
    assert result["suggestion"] == "someone@gmail.com"


def test_phone_validity_rejects_garbage():
    valid, _ = ri.phone_validity("123")
    assert valid is False


def test_team_skill_categories_aggregates_all_members_not_just_first(sample_df):
    out = ri.analyze(sample_df)
    team_group = out[out["team_id"] == "T1"]
    categories = ri.team_skill_categories(team_group)
    assert "AI/ML" in categories
    assert "Frontend" in categories or "Backend" in categories


def test_shared_ip_with_similar_registration_is_flagged(sample_df_with_ip):
    out = ri.analyze(sample_df_with_ip)
    flagged = out[out["name"].isin(["Rohan Mehta", "Rohan Mehtaa"])]
    assert all(any(r.startswith("Shared IP + Similar Registration") for r in reasons) for reasons in flagged["reasons"])
    assert (flagged["final_risk_level"] == "High Risk").all()


def test_shared_ip_with_distinct_registration_is_not_flagged(sample_df_with_ip):
    out = ri.analyze(sample_df_with_ip)
    distinct = out[out["name"].isin(["Ananya Iyer", "Devika Rao"])]
    assert not any(any(r.startswith("Shared IP") for r in reasons) for reasons in distinct["reasons"])


def test_analyze_without_ip_address_column_still_works(sample_df):
    out = ri.analyze(sample_df)
    assert "ip_address" not in out.columns or out["ip_address"].isna().all()


def test_duplicate_github_username_is_flagged(sample_df):
    df = sample_df.copy()
    df["github_username"] = ["octocat99", "octocat99", "uniqueguy", "ghostdev", "ghostdev"]
    out = ri.analyze(df)
    dup_rows = out[out["github_username"] == "octocat99"]
    assert all(any(r == "Duplicate GitHub Username" for r in reasons) for reasons in dup_rows["reasons"])
    unique_row = out[out["github_username"] == "uniqueguy"]
    assert not any("Duplicate GitHub Username" in reasons for reasons in unique_row["reasons"])


def test_analyze_without_github_username_column_still_works(sample_df):
    out = ri.analyze(sample_df)
    assert "github_username" not in out.columns


def test_evaluate_handles_mixed_null_and_string_ground_truth(sample_df):
    df = sample_df.copy()
    df.loc[0, "ground_truth_label"] = None
    out = ri.analyze(df)
    metrics = ri.evaluate(out)
    assert metrics is not None
    assert 0 <= metrics["accuracy"] <= 1


def test_blank_phone_number_is_not_treated_as_invalid(sample_df):
    df = sample_df.copy()
    df["phone_number"] = ""
    out = ri.analyze(df)
    for reasons in out["reasons"]:
        assert "Invalid Phone Format" not in reasons
        assert "Duplicate Phone Number" not in reasons
        assert "Shared Team Phone Number" not in reasons
