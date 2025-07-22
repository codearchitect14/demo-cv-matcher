from fastapi import FastAPI
from api.routers import jobs, candidates, search

app = FastAPI()

app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(search.router)

@app.get("/")
def root():
    return {"message": "Job Recommendation System is running"}
