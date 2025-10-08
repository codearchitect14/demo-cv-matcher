import os
import time
import uuid
from typing import Any, Dict, List

import json
import sys

try:
    import requests
except ImportError:
    print("This script requires the 'requests' package. Install it with: pip install requests")
    sys.exit(1)


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def wait_for_health(timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    url = f"{BASE_URL}/health"
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                print("API health: OK")
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("API health check timed out")


def create_job_public(job: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}/api/v1/jobs/public"
    r = requests.post(url, json=job, timeout=30)
    r.raise_for_status()
    return r.json()


def seed_jobs() -> List[Dict[str, Any]]:
    # 1. Create sample jobs
    print("\nCreating sample jobs (public endpoint)...")
    jobs_to_create = [
        {
            "title": "Senior Python Developer",
            "company": "Tech Solutions Inc.",
            "location": "Remote",
            "salary_min": 90000,
            "salary_max": 150000,
            "domain": "Software",
            "total_years_required": 5,
            "job_description": "Develop robust backend services using Python, FastAPI, and PostgreSQL.",
            "mandatory_skills": []  # Temporarily empty to avoid prepared statement issues
        },
        {
            "title": "Data Scientist",
            "company": "Data Insights Co.",
            "location": "New York",
            "salary_min": 100000,
            "salary_max": 160000,
            "domain": "Data Science",
            "total_years_required": 4,
            "job_description": "Build and deploy machine learning models for predictive analytics.",
            "mandatory_skills": []  # Temporarily empty to avoid prepared statement issues
        },
        {
            "title": "Frontend Engineer",
            "company": "Web Innovators",
            "location": "San Francisco",
            "salary_min": 80000,
            "salary_max": 130000,
            "domain": "Software",
            "total_years_required": 3,
            "job_description": "Develop responsive user interfaces using React and JavaScript.",
            "mandatory_skills": []  # Temporarily empty to avoid prepared statement issues
        }
    ]

    created = []
    for job in jobs_to_create:
        created_job = create_job_public(job)
        created.append(created_job)
        print(f"Created job id={created_job.get('id')} title={created_job.get('title')}")
    return created


def register_candidate() -> Dict[str, Any]:
    url = f"{BASE_URL}/api/v1/auth/register"
    unique = uuid.uuid4().hex[:8]
    payload = {
        "name": "Test User",
        "email": f"faiss_tester_{unique}@example.com",
        "password": "StrongPassw0rd!",
        "location": "Remote",
        "domain": "Software",
        "expected_salary_min": 70000,
        "expected_salary_max": 120000,
        "summary": "Python backend and data pipelines. Familiar with embeddings, FAISS, and ML."
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    print(f"Registered candidate user_id={data.get('user_id')} email={payload['email']}")
    return data


def get_job_recommendations(access_token: str, limit: int = 5) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/api/v1/recommendations/jobs?limit={limit}"
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code != 200:
        print(f"Recommendations request failed: {r.status_code} {r.text}")
        r.raise_for_status()
    return r.json()


def main():
    print(f"Testing FAISS integration against {BASE_URL}")
    wait_for_health()

    created_jobs = seed_jobs()
    # Small pause to allow embedding + FAISS add to complete
    time.sleep(2)

    auth = register_candidate()
    token = auth.get("access_token")
    if not token:
        raise RuntimeError("No access token returned from register endpoint")

    print("Requesting recommendations (semantic path uses FAISS recall)...")
    recs = get_job_recommendations(token, limit=5)

    print("\nTop recommendations:")
    for i, rec in enumerate(recs, start=1):
        job = rec.get("job") or {}
        print(
            f"{i}. job_id={rec.get('job_id')} title={getattr(job, 'title', job.get('title'))} "
            f"score={rec.get('combined_score'):.4f} method={rec.get('method')}"
        )

    print("\nDone.")


if __name__ == "__main__":
    main()


