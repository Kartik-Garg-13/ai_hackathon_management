import re

import networkx as nx
import numpy as np
import pandas as pd
import phonenumbers
from rapidfuzz import fuzz, process
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.mixture import GaussianMixture

from app.services.skill_taxonomy import (
    project_skill_alignment,
    skill_categories,
)

TRUSTED_DOMAINS = [
    "gmail.com", "outlook.com", "yahoo.com", "hotmail.com",
    "icloud.com", "protonmail.com", "rediffmail.com",
]
FAKE_PATTERNS = [
    ".xyz", ".fake", ".temp", "testmail", "temporary", "mailinator",
    "guerrillamail", "10minutemail", "disposable",
]
SHARED_IP_SIMILARITY_THRESHOLD = 0.4

NICKNAME_MAP = {
    "vishal": "vish", "abhishek": "abhi", "rajat": "raj", "manish": "mani",
    "shreya": "shrey", "kartik": "kartu", "prateek": "pratik", "nishant": "nish",
    "aryan": "ary", "divya": "div", "neha": "nehu", "rohit": "ro",
}
REV_NICKNAME = {v: k for k, v in NICKNAME_MAP.items()}
ABBREVIATED_NAME_RE = re.compile(r"^[a-z]\.\s+\w+$|^\w+\s+[a-z]\.$")

CATEGORY_RULES = [
    ("NAME_VARIATION", lambda reasons: "Abbreviated Name Format" in reasons),
    ("FAKE_EMAIL", lambda reasons: "Fake/Disposable Domain" in reasons or "Invalid Phone Format" in reasons),
    ("TYPO_EMAIL", lambda reasons: "Typo Domain" in reasons),
    ("SKILL_MISMATCH", lambda reasons: any(r.startswith("Skill Mismatch") for r in reasons)),
    ("PROJECT_DUPLICATE", lambda reasons: any(r.startswith("Overused Project Idea") for r in reasons)),
    ("INVALID_TEAM", lambda reasons: any(
        r in reasons for r in ["Missing Team Member IDs", "Duplicate Registration ID"]
    ) or any(r.startswith("Oversized Team") for r in reasons)),
    ("EXACT_DUPLICATE", lambda reasons: any(r.startswith("Duplicate of") for r in reasons)),
    ("SHARED_IP_FRAUD", lambda reasons: any(r.startswith("Shared IP + Similar Registration") for r in reasons)),
    ("SUSPICIOUS_TEAM", lambda reasons: "Rare Team Name Collision" in reasons or "Shared Team Phone Number" in reasons),
    ("EMAIL_DUPLICATE", lambda reasons: "Duplicate Email" in reasons or "Duplicate Phone Number" in reasons or "Duplicate GitHub Username" in reasons),
]


def extract_id_number(id_str) -> int:
    try:
        return int(str(id_str).split("_")[1])
    except Exception:
        return 0


def is_abbreviated_name(name: str) -> bool:
    return bool(ABBREVIATED_NAME_RE.match(name.strip().lower()))


def initials_key(name: str) -> tuple[str, str]:
    tokens = [t for t in re.sub(r"[.]", "", name).lower().split() if t]
    if len(tokens) < 2:
        return (tokens[0][0], "") if tokens else ("", "")
    return (tokens[0][0], tokens[-1])


def nickname_equiv(n1: str, n2: str) -> bool:
    tokens1, tokens2 = n1.lower().split(), n2.lower().split()
    if not tokens1 or not tokens2:
        return False
    norm1 = REV_NICKNAME.get(tokens1[0], tokens1[0])
    norm2 = REV_NICKNAME.get(tokens2[0], tokens2[0])
    return norm1 == norm2 and tokens1[-1:] == tokens2[-1:]


def split_email(email: str) -> tuple[str, str]:
    email = str(email).lower().strip()
    if "@" not in email:
        return email, ""
    local, _, domain = email.partition("@")
    return local, domain


def suspicious_char_pattern(local: str) -> bool:
    digit_ratio = sum(c.isdigit() for c in local) / max(len(local), 1)
    repeated = bool(re.search(r"(.)\1{3,}", local))
    bad_edges = local.startswith((".", "-", "_")) or local.endswith((".", "-", "_"))
    return digit_ratio > 0.5 or repeated or bad_edges


def email_intelligence(email: str) -> dict:
    local, domain = split_email(email)
    flags: list[str] = []
    score = 100
    suggestion = None

    if not domain or "." not in domain:
        return {"score": 0, "flags": ["Malformed Email"], "suggestion": None}

    if any(p in domain for p in FAKE_PATTERNS) or domain.endswith((".xyz", ".fake", ".temp")):
        return {"score": 0, "flags": ["Fake/Disposable Domain"], "suggestion": None}

    if domain.endswith((".edu", ".ac.in")) or domain in TRUSTED_DOMAINS:
        pass
    else:
        best_match, best_score, _ = process.extractOne(domain, TRUSTED_DOMAINS, scorer=fuzz.ratio)
        if 80 <= best_score < 100:
            flags.append("Typo Domain")
            suggestion = f"{local}@{best_match}"
            score -= 60
        elif best_score < 80:
            flags.append("Unrecognized Domain")
            score -= 25

    if suspicious_char_pattern(local):
        flags.append("Suspicious Character Pattern")
        score -= 20

    if len(local) < 4:
        flags.append("Very Short Local Part")
        score -= 10

    return {"score": max(score, 0), "flags": flags, "suggestion": suggestion}


def phone_validity(phone) -> tuple[bool, str]:
    raw = str(phone).strip()
    try:
        parsed = phonenumbers.parse(raw, None)
    except phonenumbers.NumberParseException:
        return False, raw
    if not phonenumbers.is_valid_number(parsed):
        return False, raw
    digits = phonenumbers.national_significant_number(parsed)
    if len(set(digits)) <= 1:
        return False, raw
    normalized = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    return True, normalized


def skill_score(skills) -> int:
    skills = str(skills)
    count = len(skills.split(","))
    if count >= 4:
        return 100
    if count == 3:
        return 80
    if count == 2:
        return 60
    return 40


def analyze(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().reset_index(drop=True)
    n = len(df)

    duplicate_penalty = {idx: 0 for idx in range(n)}
    duplicate_reasons: dict[int, list[str]] = {idx: [] for idx in range(n)}

    df["combined_text"] = (
        df["name"].fillna("") + " " + df["college"].fillna("") + " " +
        df["skills"].fillna("") + " " + df["project_idea"].fillna("")
    )
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(df["combined_text"])
    similarity_matrix = cosine_similarity(vectors)

    email_norm = df["email"].astype(str).str.lower().str.strip()
    name_norm = df["name"].astype(str).str.lower().str.strip()
    team_norm = df["team_name"].astype(str).str.lower().str.strip()
    id_num = df["id"].apply(extract_id_number)

    # with timestamps, only the later submission in a duplicate cluster is penalized
    has_timestamps = "created_at" in df.columns and df["created_at"].notna().any()
    submitted_at = pd.to_datetime(df["created_at"], errors="coerce") if has_timestamps else None

    def earliest_of(idxs: list[int]) -> int:
        if has_timestamps:
            return min(idxs, key=lambda i: (submitted_at[i], id_num[i]))
        return min(idxs, key=lambda i: id_num[i])

    key_email_name = email_norm + "||" + name_norm
    already_flagged: set[int] = set()
    for _, group in df.groupby(key_email_name).groups.items():
        idxs = list(group)
        if len(idxs) < 2:
            continue
        already_flagged.update(idxs)
        original_idx = earliest_of(idxs)
        rep_id = df.loc[original_idx, "id"]
        for idx in idxs:
            if has_timestamps and idx == original_idx:
                continue
            penalty = 100
            reason = f"Duplicate of {rep_id}"
            if team_norm[idx] == team_norm.loc[idxs[0]]:
                penalty += 25
                reason += " + Same Team"
            duplicate_penalty[idx] += penalty
            duplicate_reasons[idx].append(reason)

    email_counts = email_norm.value_counts()
    dup_emails = email_counts[email_counts > 1].index
    mask_email_dup = email_norm.isin(dup_emails)
    if has_timestamps:
        earliest_per_email = {
            email: earliest_of(list(idxs)) for email, idxs in email_norm[mask_email_dup].groupby(email_norm[mask_email_dup]).groups.items()
        }
    for idx in df.index[mask_email_dup]:
        if idx in already_flagged:
            continue
        if has_timestamps and idx == earliest_per_email[email_norm[idx]]:
            continue
        duplicate_penalty[idx] += 70
        duplicate_reasons[idx].append("Duplicate Email")

    sim = similarity_matrix.copy()
    np.fill_diagonal(sim, 0)
    max_sim_per_row = sim.max(axis=1)
    if n >= 2:
        gmm = GaussianMixture(n_components=2, random_state=42).fit(max_sim_per_row.reshape(-1, 1))
        high_cluster = np.argmax(gmm.means_.flatten())
        cluster_labels = gmm.predict(max_sim_per_row.reshape(-1, 1))
        sim_threshold = (
            max_sim_per_row[cluster_labels == high_cluster].min()
            if (cluster_labels == high_cluster).any() else 1.0
        )
        i_idx, j_idx = np.where(np.triu(sim >= sim_threshold, k=1))
        for i, j in zip(i_idx, j_idx):
            if i in already_flagged or j in already_flagged:
                continue
            duplicate_penalty[i] += 15
            duplicate_penalty[j] += 15
            duplicate_reasons[i].append("Very Similar Registration")
            duplicate_reasons[j].append("Very Similar Registration")

    if "ip_address" in df.columns:
        ip_norm = df["ip_address"].astype(str).str.strip()
        for ip, group in ip_norm[ip_norm != ""].groupby(ip_norm[ip_norm != ""]).groups.items():
            idxs = list(group)
            if len(idxs) < 2:
                continue
            for a in range(len(idxs)):
                for b in range(a + 1, len(idxs)):
                    i, j = idxs[a], idxs[b]
                    if sim[i][j] >= SHARED_IP_SIMILARITY_THRESHOLD:
                        duplicate_penalty[i] += 40
                        duplicate_penalty[j] += 40
                        duplicate_reasons[i].append(f"Shared IP + Similar Registration ({ip})")
                        duplicate_reasons[j].append(f"Shared IP + Similar Registration ({ip})")

    names_arr = name_norm.tolist()
    df["is_abbreviated_name"] = [is_abbreviated_name(nm) for nm in names_arr]

    if n >= 2:
        name_fuzzy_matrix = process.cdist(names_arr, names_arr, scorer=fuzz.token_sort_ratio, workers=-1)
        np.fill_diagonal(name_fuzzy_matrix, 0)
        fuzzy_upper = name_fuzzy_matrix[np.triu_indices_from(name_fuzzy_matrix, k=1)]
        fuzzy_nonzero = fuzzy_upper[fuzzy_upper > 0]
        fuzzy_threshold = np.quantile(fuzzy_nonzero, 0.999) if len(fuzzy_nonzero) else 100

        identity_links = []
        init_keys = [initials_key(nm) for nm in names_arr]
        fuzzy_i, fuzzy_j = np.where(np.triu(name_fuzzy_matrix >= fuzzy_threshold, k=1))
        for i, j in zip(fuzzy_i, fuzzy_j):
            identity_links.append((i, j, "Fuzzy Name Match"))

        surname_groups: dict[str, list[int]] = {}
        for idx, key in enumerate(init_keys):
            surname_groups.setdefault(key[1], []).append(idx)
        for surname, idxs in surname_groups.items():
            if surname == "" or len(idxs) < 2:
                continue
            for a in range(len(idxs)):
                for b in range(a + 1, len(idxs)):
                    i, j = idxs[a], idxs[b]
                    if df["is_abbreviated_name"].iloc[i] or df["is_abbreviated_name"].iloc[j]:
                        continue
                    if init_keys[i][0] == init_keys[j][0] and names_arr[i] != names_arr[j]:
                        identity_links.append((i, j, "Initial-Based Match"))
                    elif nickname_equiv(names_arr[i], names_arr[j]):
                        identity_links.append((i, j, "Nickname Match"))

        identity_graph = nx.Graph()
        identity_graph.add_nodes_from(range(n))
        for i, j, link_type in identity_links:
            identity_graph.add_edge(i, j, type=link_type)
        for _, group in df.groupby(key_email_name).groups.items():
            idxs = list(group)
            for a in range(len(idxs)):
                for b in range(a + 1, len(idxs)):
                    identity_graph.add_edge(idxs[a], idxs[b], type="Exact Duplicate")

        chain_id, chain_size = {}, {}
        for comp in nx.connected_components(identity_graph):
            if len(comp) > 1:
                cid = min(comp)
                for node in comp:
                    chain_id[node] = cid
                    chain_size[node] = len(comp)

        df["identity_chain_id"] = df.index.map(lambda x: chain_id.get(x, -1))
        df["identity_chain_size"] = df.index.map(lambda x: chain_size.get(x, 1))

        max_fuzzy_other = name_fuzzy_matrix.max(axis=1)
        fuzzy_baseline = np.quantile(max_fuzzy_other, 0.5)
        identity_confidence = 100 - np.clip(max_fuzzy_other - fuzzy_baseline, 0, 100 - fuzzy_baseline) * (
            50 / max(100 - fuzzy_baseline, 1)
        )
        df["identity_confidence"] = np.clip(identity_confidence, 0, 100).round(2)
    else:
        df["identity_chain_id"] = -1
        df["identity_chain_size"] = 1
        df["identity_confidence"] = 100.0
        chain_id = {}

    for idx in df.index[df["is_abbreviated_name"]]:
        duplicate_reasons[idx].append("Abbreviated Name Format")
        duplicate_penalty[idx] += 20

    email_intel = df["email"].apply(email_intelligence)
    df["email_trust_score"] = email_intel.apply(lambda d: d["score"])
    df["email_flags"] = email_intel.apply(lambda d: ", ".join(d["flags"]))
    df["email_suggested_correction"] = email_intel.apply(lambda d: d["suggestion"])
    for idx, d in email_intel.items():
        for flag in d["flags"]:
            duplicate_reasons[idx].append(flag)
        if "Fake/Disposable Domain" in d["flags"]:
            duplicate_penalty[idx] += 80
        elif "Typo Domain" in d["flags"]:
            duplicate_penalty[idx] += 30

    project_vectorizer = TfidfVectorizer(stop_words="english")
    project_vectors = project_vectorizer.fit_transform(df["project_idea"].fillna(""))
    n_clusters = max(1, min(40, df["project_idea"].nunique()))
    from sklearn.cluster import KMeans
    project_kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
    df["project_cluster"] = project_kmeans.fit_predict(project_vectors)
    cluster_sizes = df["project_cluster"].value_counts()
    df["project_cluster_size"] = df["project_cluster"].map(cluster_sizes)

    exact_idea_counts = df["project_idea"].str.lower().str.strip().value_counts()
    df["exact_idea_count"] = df["project_idea"].str.lower().str.strip().map(exact_idea_counts)
    df["project_novelty_score"] = (100 - (df["project_cluster_size"].rank(pct=True) * 100)).round(2)

    repeated_counts = exact_idea_counts[exact_idea_counts > 1]
    if len(repeated_counts) >= 4:
        log_counts = np.log(repeated_counts.values).reshape(-1, 1)
        gmm2 = GaussianMixture(n_components=2, random_state=42).fit(log_counts)
        cluster_labels2 = gmm2.predict(log_counts)
        low_cluster = np.argmin(gmm2.means_.flatten())
        popular_cutoff = np.exp(log_counts[cluster_labels2 == low_cluster].max())
    else:
        popular_cutoff = repeated_counts.max() if len(repeated_counts) else exact_idea_counts.max()

    df["project_overused_flag"] = df["exact_idea_count"].between(2, popular_cutoff)
    for idx, row in df[df["project_overused_flag"]].iterrows():
        duplicate_reasons[idx].append(f"Overused Project Idea ({row['exact_idea_count']} teams)")
        duplicate_penalty[idx] += 25

    df["team_id"] = df["id"].str.split("_").str[0]
    df["member_num"] = df["id"].apply(extract_id_number)
    team_sizes = df.groupby("team_id")["id"].size()
    df["team_size"] = df["team_id"].map(team_sizes)

    q1, q3 = team_sizes.quantile([0.25, 0.75])
    iqr = q3 - q1
    min_team = max(2, q1 - 1.5 * iqr)
    max_team = q3 + 1.5 * iqr
    df["team_undersized"] = df["team_size"] < min_team
    df["team_oversized"] = df["team_size"] > max_team
    df["duplicate_id_flag"] = df["id"].duplicated(keep=False)

    def missing_member_gap(team_id_group):
        nums = sorted(team_id_group["member_num"])
        expected = set(range(1, len(nums) + 1))
        return len(expected - set(nums)) > 0

    gap_flags = df.groupby("team_id").apply(missing_member_gap)
    df["team_has_id_gap"] = df["team_id"].map(gap_flags)

    team_name_to_ids = df.groupby("team_name")["team_id"].nunique()
    reused_counts = team_name_to_ids[team_name_to_ids > 1]
    reuse_cutoff = reused_counts.quantile(0.95) if len(reused_counts) else team_name_to_ids.max()
    suspicious_names = team_name_to_ids[team_name_to_ids > reuse_cutoff].index
    df["suspicious_team_name_reuse"] = df["team_name"].isin(suspicious_names)

    def team_skill_diversity(group):
        all_skills = [
            s.strip().lower() for skills in group["skills"].fillna("")
            for s in skills.split(",") if s.strip()
        ]
        if not all_skills:
            return 100.0
        return round(100 * len(set(all_skills)) / len(all_skills), 2)

    diversity_map = df.groupby("team_id").apply(team_skill_diversity)
    df["team_skill_diversity_score"] = df["team_id"].map(diversity_map)

    def team_health(row):
        score = 100
        if row["team_undersized"] or row["team_oversized"]:
            score -= 30
        if row["team_has_id_gap"]:
            score -= 20
        if row["suspicious_team_name_reuse"]:
            score -= 10
        if row["duplicate_id_flag"]:
            score -= 25
        score = score * 0.6 + row["team_skill_diversity_score"] * 0.4
        return round(max(score, 0), 2)

    df["team_health_score"] = df.apply(team_health, axis=1)
    for idx, row in df.iterrows():
        if row["team_oversized"]:
            duplicate_reasons[idx].append(f"Oversized Team ({row['team_size']} members)")
            duplicate_penalty[idx] += 15
        if row["team_has_id_gap"]:
            duplicate_reasons[idx].append("Missing Team Member IDs")
            duplicate_penalty[idx] += 15
        if row["suspicious_team_name_reuse"]:
            duplicate_reasons[idx].append("Rare Team Name Collision")
            duplicate_penalty[idx] += 8
        if row["duplicate_id_flag"]:
            duplicate_reasons[idx].append("Duplicate Registration ID")
            duplicate_penalty[idx] += 25

    if "phone_number" in df.columns:
        # phone is optional at signup — leaving it blank is not the same as
        # entering a garbage number, so blanks are excluded from every check below
        phone_provided = df["phone_number"].astype(str).str.strip().ne("") & df["phone_number"].notna()
        validity = df["phone_number"].apply(phone_validity)
        df["phone_valid_format"] = validity.apply(lambda t: t[0]) | ~phone_provided
        df["phone_normalized"] = validity.apply(lambda t: t[1])
        for idx in df.index[phone_provided & ~df["phone_valid_format"]]:
            duplicate_reasons[idx].append("Invalid Phone Format")
            duplicate_penalty[idx] += 40

        phone_counts = df.loc[phone_provided, "phone_normalized"].value_counts()
        dup_phones = phone_counts[phone_counts > 1].index
        # same-team phone sharing is normal; only cross-team repeats are suspicious
        phones_to_check = df[phone_provided & df["phone_normalized"].isin(dup_phones)]
        phone_team_counts = phones_to_check.groupby("phone_normalized")["team_id"].nunique()
        cross_team_dup_phones = phone_team_counts[phone_team_counts > 1].index
        for idx in df.index[phone_provided & df["phone_normalized"].isin(cross_team_dup_phones)]:
            duplicate_reasons[idx].append("Duplicate Phone Number")
            duplicate_penalty[idx] += 30

        team_phone_groups = df[phone_provided].groupby("team_id")["phone_normalized"].nunique()
        team_sizes_for_phone = df[phone_provided].groupby("team_id")["id"].size()
        shared_team_phone = team_phone_groups[
            (team_phone_groups == 1) & (team_sizes_for_phone > 1)
        ].index
        df["shared_team_phone_flag"] = phone_provided & df["team_id"].isin(shared_team_phone)
        for idx in df.index[df["shared_team_phone_flag"]]:
            duplicate_reasons[idx].append("Shared Team Phone Number")
            duplicate_penalty[idx] += 20

        df["phone_trust_score"] = 100
        df.loc[phone_provided & ~df["phone_valid_format"], "phone_trust_score"] -= 60
        df.loc[phone_provided & df["phone_normalized"].isin(cross_team_dup_phones), "phone_trust_score"] -= 40
        df["phone_trust_score"] = df["phone_trust_score"].clip(lower=0)
    else:
        df["phone_trust_score"] = 100

    if "github_username" in df.columns:
        github_norm = df["github_username"].astype(str).str.strip().str.lower()
        github_counts = github_norm[github_norm != ""].value_counts()
        dup_github = github_counts[github_counts > 1].index
        for idx in df.index[github_norm.isin(dup_github)]:
            duplicate_reasons[idx].append("Duplicate GitHub Username")
            duplicate_penalty[idx] += 30

    cat_info = df["skills"].apply(skill_categories)
    df["skill_categories"] = cat_info.apply(lambda t: ", ".join(sorted(t[0])))
    df["skill_category_count"] = cat_info.apply(lambda t: len(t[0]))
    df["skill_count"] = cat_info.apply(lambda t: t[1])
    df["skill_strength_score"] = (
        df["skill_category_count"] * 20 + df["skill_count"].clip(upper=6) * 5
    ).clip(upper=100)

    alignment = df.apply(lambda r: project_skill_alignment(r["skills"], r["project_idea"]), axis=1)
    df["skill_project_alignment_score"] = alignment.apply(lambda t: t[0])
    df["missing_critical_skill_categories"] = alignment.apply(lambda t: ", ".join(t[1]))

    no_match_score = df["skill_project_alignment_score"].min()
    for idx, row in df.iterrows():
        if row["skill_project_alignment_score"] == no_match_score and row["project_overused_flag"]:
            duplicate_reasons[idx].append(f"Skill Mismatch (missing: {row['missing_critical_skill_categories']})")
            duplicate_penalty[idx] += 25

    max_similarity_other = similarity_matrix.copy()
    np.fill_diagonal(max_similarity_other, 0)
    df["max_similarity_score"] = max_similarity_other.max(axis=1)

    anomaly_features = df[[
        "skill_count", "team_size", "email_trust_score", "max_similarity_score", "identity_confidence",
    ]].copy()
    anomaly_features["name_length"] = df["name"].str.len()

    contamination = min(0.05, max(1, int(n * 0.05)) / n) if n > 0 else 0.05
    iso_forest = IsolationForest(contamination=contamination, random_state=42, n_estimators=200)
    iso_pred = iso_forest.fit_predict(anomaly_features)
    iso_score = iso_forest.decision_function(anomaly_features)
    df["anomaly_flag"] = iso_pred == -1
    score_range = iso_score.max() - iso_score.min()
    df["anomaly_score"] = (
        100 * (iso_score.max() - iso_score) / score_range if score_range > 0 else 0
    )
    df["anomaly_score"] = df["anomaly_score"].round(2)
    for idx in df.index[df["anomaly_flag"]]:
        duplicate_reasons[idx].append("Statistical Anomaly (Isolation Forest)")
        duplicate_penalty[idx] += 10

    distance_matrix = np.clip(1 - similarity_matrix, 0, None)
    min_samples = 3
    if n > min_samples:
        knn_seed = distance_matrix.copy()
        np.fill_diagonal(knn_seed, 1.0)
        knn_dist = np.sort(knn_seed, axis=1)[:, min_samples - 1]
        eps = np.quantile(knn_dist, 0.05)
        np.fill_diagonal(distance_matrix, 0)
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
        df["fraud_ring_id"] = dbscan.fit_predict(distance_matrix)
    else:
        df["fraud_ring_id"] = -1

    ring_sizes = df[df["fraud_ring_id"] != -1].groupby("fraud_ring_id").size()
    df["fraud_ring_size"] = df["fraud_ring_id"].map(ring_sizes).fillna(1).astype(int)
    df["is_fraud_ring_member"] = df["fraud_ring_id"] != -1
    for idx, row in df[df["is_fraud_ring_member"]].iterrows():
        duplicate_reasons[idx].append(f"Fraud Ring #{row['fraud_ring_id']} ({row['fraud_ring_size']} members)")
        duplicate_penalty[idx] += 20

    df["reasons"] = df.index.map(lambda x: list(dict.fromkeys(duplicate_reasons[x])))

    def final_trust(row):
        base = (
            0.18 * row["email_trust_score"] +
            0.12 * row["phone_trust_score"] +
            0.15 * row["skill_strength_score"] +
            0.15 * row["skill_project_alignment_score"] +
            0.15 * row["identity_confidence"] +
            0.15 * row["team_health_score"] +
            0.10 * (100 - row["anomaly_score"])
        )
        penalty = min(duplicate_penalty[row.name], 90)
        return round(max(0, min(100, base - penalty)), 2)

    df["final_trust_score"] = df.apply(final_trust, axis=1)

    def final_risk(score):
        if score >= 80:
            return "Low Risk"
        if score >= 55:
            return "Medium Risk"
        return "High Risk"

    df["final_risk_level"] = df["final_trust_score"].apply(final_risk)

    def confidence(row):
        evidence = len(row["reasons"])
        return round(min(100, 50 + evidence * 12), 2)

    df["confidence_score"] = df.apply(confidence, axis=1)

    def explain(row):
        if not row["reasons"]:
            return f"{row['final_risk_level']} | Trust {row['final_trust_score']} | Confidence {row['confidence_score']}\nNo red flags."
        bullets = "\n".join(f"  - {r}" for r in row["reasons"])
        return f"{row['final_risk_level']} | Trust {row['final_trust_score']} | Confidence {row['confidence_score']}\nReasons:\n{bullets}"

    df["explanation"] = df.apply(explain, axis=1)

    df["predicted_label"] = df["reasons"].apply(predict_category)

    df["participant_quality_score"] = (
        0.5 * df["final_trust_score"] +
        0.3 * df["skill_strength_score"] +
        0.2 * df["project_novelty_score"]
    ).round(2)

    return df


def team_skill_categories(group: pd.DataFrame) -> str:
    categories: set[str] = set()
    for value in group["skill_categories"].fillna(""):
        categories.update(c.strip() for c in value.split(",") if c.strip())
    return ", ".join(sorted(categories))


def predict_category(reasons: list[str]) -> str:
    for label, rule in CATEGORY_RULES:
        if rule(reasons):
            return label
    return "GENUINE"


def evaluate(df: pd.DataFrame) -> dict | None:
    if "ground_truth_label" not in df.columns or df["ground_truth_label"].isna().all():
        return None

    df = df[df["ground_truth_label"].notna()]

    report = classification_report(
        df["ground_truth_label"], df["predicted_label"], zero_division=0, output_dict=True
    )
    acc = accuracy_score(df["ground_truth_label"], df["predicted_label"])
    prec, rec, f1, _ = precision_recall_fscore_support(
        df["ground_truth_label"], df["predicted_label"], average="macro", zero_division=0
    )
    labels_order = sorted(df["ground_truth_label"].unique())
    cm = confusion_matrix(df["ground_truth_label"], df["predicted_label"], labels=labels_order)

    y_true_binary = (df["ground_truth_label"] != "GENUINE").astype(int)
    y_score_binary = 100 - df["final_trust_score"]
    auc = None
    if y_true_binary.nunique() > 1:
        auc = roc_auc_score(y_true_binary, y_score_binary)

    return {
        "accuracy": round(acc, 4),
        "macro_precision": round(prec, 4),
        "macro_recall": round(rec, 4),
        "macro_f1": round(f1, 4),
        "roc_auc_fraud_vs_genuine": round(auc, 4) if auc is not None else None,
        "labels": labels_order,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }
