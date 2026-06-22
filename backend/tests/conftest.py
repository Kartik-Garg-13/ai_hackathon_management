import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

FIXTURE_ROWS = [
    ("T1_001", "Aman Gupta", "amangupta1@gmail.com", "IIT Delhi", "Python,React,FastAPI", "AI Resume Screener", "Alpha1", "GENUINE", "+919876543210"),
    ("T1_002", "Riya Shah", "riyashah2@gmail.com", "IIT Delhi", "Python,TensorFlow,NLP", "AI Resume Screener", "Alpha1", "GENUINE", "+919876543211"),
    ("T2_001", "Karan Verma", "karanverma3@yahoo.com", "NIT Trichy", "React,Node.js,JavaScript", "Web Portal for Farmers", "Beta2", "GENUINE", "+919876543212"),
    ("T3_001", "Fake User", "fakeuser4@testmail.xyz", "Unknown College", "Python", "Generic App", "Gamma3", "FAKE_EMAIL", "123"),
    ("T3_002", "Fake User", "fakeuser4@testmail.xyz", "Unknown College", "Python", "Generic App", "Gamma3", "FAKE_EMAIL", "123"),
]

COLUMNS = ["id", "name", "email", "college", "skills", "project_idea", "team_name", "ground_truth_label", "phone_number"]


@pytest.fixture
def sample_df():
    return pd.DataFrame(FIXTURE_ROWS, columns=COLUMNS)


IP_FIXTURE_ROWS = [
    ("T1_001", "Rohan Mehta", "rohanmehta@gmail.com", "Demo Institute", "Python,React,FastAPI", "AI Powered Campus Navigation App", "SquadA", "SHARED_IP_FRAUD", "+919900000001", "203.0.113.50"),
    ("T2_001", "Rohan Mehtaa", "rohanmehtaa@gmail.com", "Demo Institute", "Python,React,FastAPI", "AI Powered Campus Navigation Application", "SquadB", "SHARED_IP_FRAUD", "+919900000002", "203.0.113.50"),
    ("T3_001", "Ananya Iyer", "ananya@gmail.com", "Demo Institute", "Java,Spring Boot,MySQL", "Blockchain Based Land Registry", "SquadC", "GENUINE", "+919900000003", "198.51.100.77"),
    ("T4_001", "Devika Rao", "devika@gmail.com", "Demo Institute", "Flutter,Firebase,Dart", "Mental Health Companion Mobile App", "SquadD", "GENUINE", "+919900000004", "198.51.100.77"),
]

IP_COLUMNS = COLUMNS + ["ip_address"]


@pytest.fixture
def sample_df_with_ip():
    return pd.DataFrame(IP_FIXTURE_ROWS, columns=IP_COLUMNS)
