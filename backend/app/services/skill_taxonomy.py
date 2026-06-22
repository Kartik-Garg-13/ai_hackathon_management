from rapidfuzz import fuzz, process

SKILL_TAXONOMY = {
    "python": "Programming", "java": "Programming", "c++": "Programming", "rust": "Programming",
    "javascript": "Programming", "go": "Programming", "typescript": "Programming",
    "tensorflow": "AI/ML", "pytorch": "AI/ML", "deep learning": "AI/ML", "machine learning": "AI/ML",
    "bert": "AI/ML", "hugging face": "AI/ML", "nlp": "AI/ML", "scikit-learn": "AI/ML",
    "data science": "AI/ML", "opencv": "AI/ML", "keras": "AI/ML", "langchain": "AI/ML",
    "react": "Frontend", "vue": "Frontend", "angular": "Frontend", "ui/ux": "Frontend",
    "figma": "Frontend", "next.js": "Frontend", "html": "Frontend", "css": "Frontend", "bootstrap": "Frontend",
    "node.js": "Backend", "express.js": "Backend", "django": "Backend", "flask": "Backend",
    "fastapi": "Backend", "spring boot": "Backend", "graphql": "Backend",
    "docker": "Cloud/DevOps", "kubernetes": "Cloud/DevOps", "azure": "Cloud/DevOps",
    "aws": "Cloud/DevOps", "gcp": "Cloud/DevOps", "linux": "Cloud/DevOps",
    "pandas": "Data", "numpy": "Data", "sql": "Data", "postgresql": "Data", "mongodb": "Data", "redis": "Data",
    "flutter": "Mobile", "swift": "Mobile", "kotlin": "Mobile", "ios": "Mobile", "android": "Mobile",
    "blockchain": "Emerging Tech", "solidity": "Emerging Tech", "streamlit": "Emerging Tech",
    "photoshop": "Design/Creative", "illustrator": "Design/Creative",
    "autocad": "Engineering/CAD", "solidworks": "Engineering/CAD",
    "tally": "Business/Finance",
    "cybersecurity": "Security",
}
KNOWN_SKILLS = list(SKILL_TAXONOMY.keys())

PROJECT_CATEGORY_KEYWORDS = {
    "AI/ML": ["ai", "machine learning", "deep learning", "nlp", "deepfake", "detection",
              "prediction", "classifier", "chatbot", "recommender"],
    "Frontend": ["portal", "website", "dashboard", "ui"],
    "Backend": ["platform", "system", "api"],
    "Mobile": ["app"],
    "Cloud/DevOps": ["cloud", "infrastructure", "optimizer", "network"],
    "Data": ["analyzer", "analytics", "data"],
    "Emerging Tech": ["blockchain", "smart contract", "dao", "decentralized", "crypto"],
    "Security": ["fraud", "phishing", "security", "audit"],
}

_skill_cache: dict[str, str] = {}


def categorize_skill(skill: str) -> str:
    s = skill.strip().lower()
    if s in SKILL_TAXONOMY:
        return SKILL_TAXONOMY[s]
    if s in _skill_cache:
        return _skill_cache[s]
    match, score, _ = process.extractOne(s, KNOWN_SKILLS, scorer=fuzz.ratio)
    category = SKILL_TAXONOMY[match] if score >= 80 else "Other"
    _skill_cache[s] = category
    return category


def skill_categories(skills_str: str) -> tuple[set[str], int]:
    skills = [s.strip() for s in str(skills_str).split(",") if s.strip()]
    return {categorize_skill(s) for s in skills}, len(skills)


def project_required_categories(project_idea: str) -> set[str]:
    project_l = str(project_idea).lower()
    return {cat for cat, kws in PROJECT_CATEGORY_KEYWORDS.items() if any(k in project_l for k in kws)}


def project_skill_alignment(skills_str: str, project: str) -> tuple[int, list[str]]:
    cats, _ = skill_categories(skills_str)
    required = project_required_categories(project)
    if not required:
        return 70, []
    matched = required & cats
    missing = required - cats
    score = 100 if matched else 25
    return score, sorted(missing)
