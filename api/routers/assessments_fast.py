from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

# Fast mock endpoints for MCQs and Assessments

router = APIRouter(prefix="/assessments-fast", tags=["Assessments Fast"])

# Pydantic models
class MCQSubmitRequest(BaseModel):
    application_id: int
    answers: List[str]
    cheat_attempts: int = 0

# In-memory stores (mock persistence)
job_mcqs_store: Dict[int, List[Dict[str, Any]]] = {}
assessments_store: Dict[int, Dict[str, Any]] = {}  # key: application_id

# Database functions for persistent storage
async def save_assessment_to_db(assessment_data):
    """Save assessment data to database"""
    try:
        from config.connection_pool import global_pool
        await global_pool.execute("""
            INSERT INTO assessments (application_id, candidate_id, job_id, status, score, 
                                   start_time, completion_time, cheat_attempts, mcq_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (application_id) DO UPDATE SET
                status = EXCLUDED.status,
                score = EXCLUDED.score,
                completion_time = EXCLUDED.completion_time,
                cheat_attempts = EXCLUDED.cheat_attempts
        """, 
            assessment_data["application_id"],
            assessment_data["candidate_id"], 
            assessment_data["job_id"],
            assessment_data["status"],
            assessment_data["score"],
            assessment_data.get("start_time"),
            assessment_data.get("completion_time"),
            assessment_data["cheat_attempts"],
            assessment_data["mcq_count"]
        )
    except Exception as e:
        print(f"❌ Error saving assessment to DB: {e}")

async def load_assessment_from_db(application_id):
    """Load assessment data from database"""
    try:
        from config.connection_pool import global_pool
        row = await global_pool.fetchrow("""
            SELECT application_id, candidate_id, job_id, status, score,
                   start_time, completion_time, cheat_attempts, mcq_count
            FROM assessments WHERE application_id = $1
        """, application_id)
        
        if row:
            result = {
                "application_id": row["application_id"],
                "candidate_id": row["candidate_id"],
                "job_id": row["job_id"],
                "status": row["status"],
                "score": row["score"],
                "start_time": row["start_time"].isoformat() if row["start_time"] else None,
                "completion_time": row["completion_time"].isoformat() if row["completion_time"] else None,
                "cheat_attempts": row["cheat_attempts"],
                "mcq_count": row["mcq_count"],
                "valid_until": None  # Not stored in DB for now
            }
            return result
    except Exception as e:
        print(f"❌ Error loading assessment from DB: {e}")
    return None

async def save_mcqs_to_db(job_id, mcqs):
    """Save MCQs to database"""
    try:
        from config.connection_pool import global_pool
        # Clear existing MCQs for this job
        await global_pool.execute("DELETE FROM job_mcqs WHERE job_id = $1", job_id)
        
        # Insert new MCQs
        for i, mcq in enumerate(mcqs):
            await global_pool.execute("""
                INSERT INTO job_mcqs (job_id, question_number, question, option_a, option_b, option_c, option_d, correct_answer)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
                job_id, i + 1, mcq["question"], 
                mcq["options"]["A"], mcq["options"]["B"], mcq["options"]["C"], mcq["options"]["D"],
                mcq["correct"]
            )
        print(f"Saved {len(mcqs)} MCQs to database for job {job_id}")
    except Exception as e:
        print(f"Error saving MCQs to DB: {e}")

async def load_mcqs_from_db(job_id):
    """Load MCQs from database"""
    try:
        from config.connection_pool import global_pool
        rows = await global_pool.fetch("""
            SELECT question, option_a, option_b, option_c, option_d, correct_answer
            FROM job_mcqs WHERE job_id = $1 ORDER BY question_number
        """, job_id)
        
        mcqs = []
        for row in rows:
            mcqs.append({
                "question": row["question"],
                "options": {
                    "A": row["option_a"],
                    "B": row["option_b"], 
                    "C": row["option_c"],
                    "D": row["option_d"]
                },
                "correct": row["correct_answer"]
            })
        print(f"Loaded {len(mcqs)} MCQs from database for job {job_id}")
        return mcqs
    except Exception as e:
        print(f"Error loading MCQs from DB: {e}")
        return []

# Add some test MCQs for debugging
def _init_test_mcqs():
    """Initialize with test MCQs for common job IDs"""
    test_mcqs = [
        {
            "question": "What is React?",
            "options": {
                "A": "A JavaScript library for building user interfaces",
                "B": "A database management system", 
                "C": "A programming language",
                "D": "A web server"
            },
            "correct": "A"
        },
        {
            "question": "What is the purpose of useState in React?",
            "options": {
                "A": "To fetch data from APIs",
                "B": "To manage component state",
                "C": "To style components",
                "D": "To handle routing"
            },
            "correct": "B"
        },
        {
            "question": "What does JSX stand for?",
            "options": {
                "A": "JavaScript XML",
                "B": "Java Script Extension",
                "C": "JSON Syntax Extension",
                "D": "JavaScript Extension"
            },
            "correct": "A"
        },
        {
            "question": "What is the virtual DOM?",
            "options": {
                "A": "A real DOM element",
                "B": "A JavaScript representation of the DOM",
                "C": "A CSS framework",
                "D": "A database table"
            },
            "correct": "B"
        },
        {
            "question": "What is a React component?",
            "options": {
                "A": "A CSS file",
                "B": "A reusable piece of UI",
                "C": "A database query",
                "D": "A server endpoint"
            },
            "correct": "B"
        }
    ]
    
    # Add test MCQs for job IDs that commonly appear in applications
    for job_id in [11, 35, 52]:  # Common job IDs from your logs
        job_mcqs_store[job_id] = test_mcqs

# Initialize test MCQs
_init_test_mcqs()

# Initialize database tables on startup
async def init_assessment_tables():
    """Create assessment tables if they don't exist"""
    try:
        from config.connection_pool import global_pool
        
        # Create assessments table
        await global_pool.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                application_id INTEGER PRIMARY KEY,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                score DECIMAL(5,2),
                start_time TIMESTAMP,
                completion_time TIMESTAMP,
                cheat_attempts INTEGER DEFAULT 0,
                mcq_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create job_mcqs table
        await global_pool.execute("""
            CREATE TABLE IF NOT EXISTS job_mcqs (
                id SERIAL PRIMARY KEY,
                job_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer CHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id, question_number)
            )
        """)
        
        print("✅ Assessment database tables initialized")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize assessment tables: {e}")

# Run table initialization
import asyncio
try:
    asyncio.create_task(init_assessment_tables())
except Exception:
    pass

def _now_iso() -> str:
    return datetime.utcnow().isoformat()

@router.post("/mcqs/{job_id}")
async def upsert_job_mcqs(job_id: int, mcqs: List[Dict[str, Any]]):
    """Create/replace up to 20 MCQs for a job.
    Each MCQ must contain: question, options {A,B,C,D}, correct (A/B/C/D)
    """
    print(f"=== SAVE MCQs REQUEST ===")
    print(f"Job ID: {job_id}")
    print(f"MCQs received: {len(mcqs) if mcqs else 0}")
    print(f"MCQs data: {mcqs[:2] if mcqs else 'None'}")  # Show first 2 MCQs
    
    if not isinstance(mcqs, list) or len(mcqs) == 0:
        print(f"ERROR: MCQs list required")
        raise HTTPException(status_code=400, detail="MCQs list required")
    if len(mcqs) > 20:
        print(f"ERROR: Too many MCQs: {len(mcqs)}")
        raise HTTPException(status_code=400, detail="Maximum 20 MCQs allowed")

    normalized: List[Dict[str, Any]] = []
    for idx, q in enumerate(mcqs, start=1):
        question = (q.get("question") or "").strip()
        options = q.get("options") or {}
        correct = (q.get("correct") or "").strip().upper()
        if not question or not isinstance(options, dict):
            print(f"ERROR: Invalid MCQ at index {idx}: question='{question}', options={options}")
            raise HTTPException(status_code=400, detail=f"Invalid MCQ at index {idx}")
        for key in ["A", "B", "C", "D"]:
            if key not in options or not str(options[key]).strip():
                print(f"ERROR: Option {key} missing at index {idx}: {options}")
                raise HTTPException(status_code=400, detail=f"Option {key} missing at index {idx}")
        if correct not in ["A", "B", "C", "D"]:
            print(f"ERROR: Correct option invalid at index {idx}: '{correct}'")
            raise HTTPException(status_code=400, detail=f"Correct option invalid at index {idx}")
        normalized.append({"question": question, "options": {k: str(options[k]) for k in ["A","B","C","D"]}, "correct": correct})

    # Save to both memory store and database
    job_mcqs_store[job_id] = normalized
    await save_mcqs_to_db(job_id, normalized)
    
    print(f"SUCCESS: Saved {len(normalized)} MCQs for job {job_id}")
    print(f"Store now contains: {list(job_mcqs_store.keys())}")
    return {"job_id": job_id, "count": len(normalized), "message": "MCQs saved"}


@router.get("/mcqs/{job_id}")
async def get_job_mcqs(job_id: int):
    # Try memory store first, then database
    mcqs = job_mcqs_store.get(job_id, [])
    if not mcqs:
        mcqs = await load_mcqs_from_db(job_id)
        if mcqs:
            job_mcqs_store[job_id] = mcqs  # Cache in memory
    
    print(f"=== GET MCQs REQUEST ===")
    print(f"Job ID: {job_id}")
    print(f"MCQs found: {len(mcqs)}")
    print(f"Store contains jobs: {list(job_mcqs_store.keys())}")
    return {"job_id": job_id, "mcqs": mcqs}

@router.get("/mcqs")
async def list_all_jobs_with_mcqs():
    """Debug endpoint to see which jobs have MCQs"""
    return {"jobs_with_mcqs": list(job_mcqs_store.keys()), "store": job_mcqs_store}

@router.get("/debug/db-status")
async def debug_database_status():
    """Debug endpoint to check database table status"""
    try:
        from config.connection_pool import global_pool
        
        # Check if tables exist
        tables = await global_pool.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('assessments', 'job_mcqs')
        """)
        
        table_names = [row['table_name'] for row in tables]
        
        # Count records in each table
        assessments_count = 0
        mcqs_count = 0
        
        if 'assessments' in table_names:
            assessments_count = await global_pool.fetchval("SELECT COUNT(*) FROM assessments")
        
        if 'job_mcqs' in table_names:
            mcqs_count = await global_pool.fetchval("SELECT COUNT(*) FROM job_mcqs")
        
        return {
            "tables_exist": table_names,
            "assessments_count": assessments_count,
            "mcqs_count": mcqs_count,
            "memory_assessments": list(assessments_store.keys()),
            "memory_mcqs": list(job_mcqs_store.keys())
        }
        
    except Exception as e:
        return {"error": str(e)}


@router.post("/assign")
async def assign_assessment(
    application_id: int,
    candidate_id: int,
    job_id: int,
    validity_hours: int = 24
):
    print(f"Assign assessment request: application_id={application_id}, job_id={job_id}")
    
    # Check if assessment already exists in database
    existing_assessment = await load_assessment_from_db(application_id)
    if existing_assessment:
        print(f"Assessment already exists in database for application {application_id}")
        assessments_store[application_id] = existing_assessment
        return existing_assessment
    
    # Check if assessment exists in memory store
    if application_id in assessments_store:
        print(f"Assessment already exists in memory for application {application_id}")
        return assessments_store[application_id]
    
    # Load MCQs (try memory first, then database)
    mcqs = job_mcqs_store.get(job_id, [])
    if not mcqs:
        mcqs = await load_mcqs_from_db(job_id)
        if mcqs:
            job_mcqs_store[job_id] = mcqs
    
    print(f"Available MCQs for job {job_id}: {len(mcqs)}")
    
    if len(mcqs) == 0:
        print(f"No MCQs found for job {job_id}")
        raise HTTPException(status_code=400, detail="No MCQs configured for this job")

    assessment = {
        "application_id": application_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "status": "pending",
        "score": None,
        "start_time": None,
        "completion_time": None,
        "valid_until": (datetime.utcnow() + timedelta(hours=validity_hours)).isoformat(),
        "cheat_attempts": 0,
        "mcq_count": len(mcqs)
    }
    
    # Store in both memory and database
    assessments_store[application_id] = assessment
    await save_assessment_to_db(assessment)
    
    print(f"Created assessment: {assessment}")
    return assessment


@router.get("/assigned")
async def get_assigned(application_id: int):
    # Try memory store first, then database
    asses = assessments_store.get(application_id)
    if not asses:
        asses = await load_assessment_from_db(application_id)
        if asses:
            assessments_store[application_id] = asses  # Cache in memory
    
    if not asses:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    payload = dict(asses)
    
    # Load MCQs for this assessment
    mcqs = job_mcqs_store.get(asses["job_id"], [])
    if not mcqs:
        mcqs = await load_mcqs_from_db(asses["job_id"])
        if mcqs:
            job_mcqs_store[asses["job_id"]] = mcqs
    
    payload["mcqs"] = mcqs
    return payload

@router.get("/status/{application_id}")
async def get_assessment_status(application_id: int):
    """Get assessment status for an application (for My Applications page)"""
    # Try memory store first, then database
    asses = assessments_store.get(application_id)
    if not asses:
        asses = await load_assessment_from_db(application_id)
        if asses:
            assessments_store[application_id] = asses  # Cache in memory
    
    if not asses:
        return {"has_assessment": False}
    
    return {
        "has_assessment": True,
        "status": asses.get("status", "pending"),
        "score": asses.get("score"),
        "completion_time": asses.get("completion_time"),
        "cheat_attempts": asses.get("cheat_attempts", 0)
    }


@router.post("/start")
async def start_assessment(application_id: int):
    asses = assessments_store.get(application_id)
    if not asses:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if asses.get("status") not in ["pending", "in_progress"]:
        raise HTTPException(status_code=400, detail="Assessment already completed")
    asses["status"] = "in_progress"
    if not asses.get("start_time"):
        asses["start_time"] = _now_iso()
    return asses


@router.post("/submit")
async def submit_assessment(request: MCQSubmitRequest):
    print(f"Submit assessment request: {request}")
    print(f"Available assessments: {list(assessments_store.keys())}")
    
    asses = assessments_store.get(request.application_id)
    if not asses:
        print(f"Assessment not found for application_id: {request.application_id}")
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Prevent multiple submissions - if already completed, return existing result
    if asses.get("status") == "completed":
        print(f"Assessment already completed for application_id: {request.application_id}, returning existing result")
        return asses

    mcqs = job_mcqs_store.get(asses["job_id"], [])
    total = max(len(mcqs), 1)
    correct_count = 0
    
    # Only count answers if they exist and are not empty
    if request.answers and len(request.answers) > 0:
        for i, q in enumerate(mcqs):
            if i < len(request.answers) and str(request.answers[i]).upper() == q.get("correct"):
                correct_count += 1
    else:
        # If no answers provided, treat as failed attempt
        correct_count = 0
    
    score = round((correct_count / total) * 100, 1)

    print(f"Assessment scoring: {correct_count}/{total} correct = {score}%")

    asses["status"] = "completed"
    asses["score"] = score
    asses["completion_time"] = _now_iso()
    asses["cheat_attempts"] = request.cheat_attempts

    # Save to database
    await save_assessment_to_db(asses)

    # Update application in mock storage if available
    try:
        from api.routers.applications_fast import mock_applications_storage
        for app in mock_applications_storage:
            if app.get("id") == request.application_id:
                app["assessment"] = {k: asses[k] for k in ["status","score","start_time","completion_time","cheat_attempts"]}
                if score >= 50 and request.cheat_attempts == 0:
                    app["status"] = "INTERVIEW_SCHEDULED"
                else:
                    app["status"] = "REJECTED"
                break
    except Exception:
        pass

    return asses


