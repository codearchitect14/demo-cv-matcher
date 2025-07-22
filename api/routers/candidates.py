from fastapi import APIRouter

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get("/")
def get_candidates():
    return {"message": "List of candidates"}
