# Today's date: 25/07/2025
from fastapi import FastAPI
from api.routers import jobs, candidates, search, applications  # Added applications router (Issue #11)

app = FastAPI(
    title="Job Recommendation System",
    description="A comprehensive job recommendation system with candidate matching",
    version="1.0.0"
)

# Include all routers
app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(search.router)
app.include_router(applications.router)  # Added missing applications router (Issue #11)

@app.get("/")
def root():
    return {"message": "Job Recommendation System is running"}
