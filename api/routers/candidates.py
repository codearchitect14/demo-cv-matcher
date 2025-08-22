#Today's date: 25/07/2025
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db_session
from models.candidate import Candidate, CandidateExperience
from db.crud.candidate import candidate as candidate_crud
from db.crud.application import application as application_crud
from api.routers.auth import get_current_user
from schemas.candidate import CandidateCreate, CandidateUpdate, CandidateResponse, CandidateResponseSimple, CandidateExperienceCreate, CandidateExperienceUpdate

router = APIRouter(tags=["Candidates"])

@router.post("/", response_model=CandidateResponse)
async def create_candidate(
    candidate_data: CandidateCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new candidate profile"""
    try:
        # Check if candidate with this email already exists
        existing_candidate = await candidate_crud.get_by_email(db, email=candidate_data.email)
        if existing_candidate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already in use. Please use a different email address."
            )
        
        # Create the candidate
        candidate = await candidate_crud.create(db, obj_in=candidate_data)
        # Get the candidate with loaded relationships
        candidate_with_relations = await candidate_crud.get_with_experiences(db, candidate.id)
        return candidate_with_relations
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Check if it's a database constraint violation
        error_str = str(e).lower()
        if "unique" in error_str and "email" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already in use. Please use a different email address."
            )
        elif "not null" in error_str and "email" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is required."
            )
        else:
            # Log the actual error for debugging but return user-friendly message
            print(f"Create candidate error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create candidate. Please try again later."
            )

@router.get("/", response_model=List[CandidateResponse])
async def get_all_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search candidates by name or email"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all candidates with pagination and optional search"""
    try:
        if search:
            # Use fuzzy search for name and email - returns dict format
            candidates = await candidate_crud.search_by_name_or_email(db, search, skip=skip, limit=limit)
            return candidates  # Already in correct format
        else:
            # Use simple get_multi to avoid prepared statement conflicts
            candidates = await candidate_crud.get_multi(db, skip=skip, limit=limit)
            # Convert to dict format to avoid relationship issues
            candidate_dicts = []
            for candidate in candidates:
                candidate_dict = {
                    "id": candidate.id,
                    "name": candidate.name,
                    "email": candidate.email,
                    "location": candidate.location,
                    "domain": candidate.domain,
                    "expected_salary_min": candidate.expected_salary_min,
                    "expected_salary_max": candidate.expected_salary_max,
                    "summary": candidate.summary,
                    "consent_given": candidate.consent_given,
                    "created_at": candidate.created_at,
                    "updated_at": candidate.updated_at,
                    "experiences": []  # Empty list to satisfy schema
                }
                candidate_dicts.append(candidate_dict)
            return candidate_dicts
    except Exception as e:
        print(f"Get all candidates error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidates. Please try again later."
        )

@router.get("/public", response_model=List[CandidateResponseSimple])
async def get_all_candidates_public(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all candidates with pagination (public endpoint)"""
    try:
        # Use simple get_multi to avoid prepared statement conflicts
        candidates = await candidate_crud.get_multi(db, skip=skip, limit=limit)
        return candidates
    except Exception as e:
        print(f"Get all candidates public error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidates. Please try again later."
        )

@router.get("/me", response_model=CandidateResponse)
async def get_my_profile(
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current user's profile"""
    try:
        # Get the candidate with loaded relationships
        candidate_with_relations = await candidate_crud.get_with_experiences(db, current_user.id)
        return candidate_with_relations
    except Exception as e:
        print(f"Get my profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile. Please try again later."
        )

@router.put("/me", response_model=CandidateResponse)
async def update_my_profile(
    candidate_data: CandidateUpdate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update current user's profile"""
    try:
        # Update the candidate
        updated_candidate = await candidate_crud.update(db, db_obj=current_user, obj_in=candidate_data)
        # Get the updated candidate with loaded relationships
        candidate_with_relations = await candidate_crud.get_with_experiences(db, current_user.id)
        return candidate_with_relations
    except Exception as e:
        print(f"Update my profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile. Please try again later."
        )

@router.post("/test-upload")
async def test_upload(
    test_file: UploadFile = File(...),
    current_user: Candidate = Depends(get_current_user)
):
    """Test endpoint for file upload functionality"""
    try:
        return {
            "message": "Test upload successful",
            "filename": test_file.filename,
            "size": test_file.size,
            "content_type": test_file.content_type,
            "candidate_id": current_user.id
        }
    except Exception as e:
        print(f"Test upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test upload failed"
        )

@router.post("/upload-cv")
async def upload_cv(
    cv_file: UploadFile = File(...),  # Remove max_length parameter
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Upload CV for current user"""
    try:
        # Validate file type - only PDF, DOC, and DOCX files allowed
        if not cv_file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF, DOC, and DOCX files are allowed for CV upload."
            )
        
        # Validate file size (max 100MB)
        if cv_file.size and cv_file.size > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 100MB."
            )
        
        # Read file content
        file_content = await cv_file.read()
        
        # In a real application, you would:
        # 1. Save the file to a secure location (e.g., S3, local storage)
        # 2. Parse the CV content using OCR or text extraction
        # 3. Extract skills, experience, and other relevant information
        # 4. Update the candidate's profile with extracted information
        
        # For now, we'll just return a success message
        return {
            "message": "CV uploaded successfully",
            "filename": cv_file.filename,
            "size": len(file_content),
            "candidate_id": current_user.id,
            "file_type": cv_file.content_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload CV error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload CV. Please try again later."
        )

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get candidate profile by ID"""
    try:
        # First get the basic candidate
        candidate = await candidate_crud.get(db, id=candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        # Then get experiences separately to avoid prepared statement conflicts
        experiences = await candidate_crud.get_experiences(db, candidate_id=candidate_id)
        
        # Manually construct the response with experiences
        candidate_dict = {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "location": candidate.location,
            "domain": candidate.domain,
            "expected_salary_min": candidate.expected_salary_min,
            "expected_salary_max": candidate.expected_salary_max,
            "summary": candidate.summary,
            "consent_given": candidate.consent_given,
            "created_at": candidate.created_at,
            "updated_at": candidate.updated_at,
            "experiences": experiences
        }
        
        return candidate_dict
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Get candidate error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidate profile. Please try again later."
        )

@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: int,
    candidate_data: CandidateUpdate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update candidate profile (only own profile)"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update own profile"
            )
        
        # Update the candidate
        candidate = await candidate_crud.update(db, db_obj=current_user, obj_in=candidate_data)
        
        # Get experiences separately to avoid prepared statement conflicts
        experiences = await candidate_crud.get_experiences(db, candidate_id=candidate.id)
        
        # Manually construct the response with experiences
        candidate_dict = {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "location": candidate.location,
            "domain": candidate.domain,
            "expected_salary_min": candidate.expected_salary_min,
            "expected_salary_max": candidate.expected_salary_max,
            "summary": candidate.summary,
            "consent_given": candidate.consent_given,
            "created_at": candidate.created_at,
            "updated_at": candidate.updated_at,
            "experiences": experiences
        }
        
        return candidate_dict
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Update candidate error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile. Please try again later."
        )

@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete candidate profile (GDPR compliance)"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete own profile"
            )
        
        # Delete all related data (applications, interactions, experiences)
        await candidate_crud.delete(db, id=candidate_id)
        
        return {"message": "Candidate profile deleted successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Delete candidate error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile. Please try again later."
        )

@router.post("/{candidate_id}/experience", response_model=CandidateResponse)
async def add_candidate_experience(
    candidate_id: int,
    experience_data: CandidateExperienceCreate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Add experience to candidate profile"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only add experience to own profile"
            )
        
        # Convert Pydantic model to dict
        experience_dict = experience_data.dict()
        
        # Add experience using the CRUD method
        await candidate_crud.add_experience(
            db, candidate_id=candidate_id, experience_data=experience_dict
        )
        
        # Get the updated candidate and experiences separately
        candidate = await candidate_crud.get(db, id=candidate_id)
        experiences = await candidate_crud.get_experiences(db, candidate_id=candidate_id)
        
        # Manually construct the response
        candidate_dict = {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "location": candidate.location,
            "domain": candidate.domain,
            "expected_salary_min": candidate.expected_salary_min,
            "expected_salary_max": candidate.expected_salary_max,
            "summary": candidate.summary,
            "consent_given": candidate.consent_given,
            "created_at": candidate.created_at,
            "updated_at": candidate.updated_at,
            "experiences": experiences
        }
        
        return candidate_dict
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Add experience error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add experience. Please try again later."
        )

@router.put("/{candidate_id}/experience/{experience_id}")
async def update_candidate_experience(
    candidate_id: int,
    experience_id: int,
    experience_data: CandidateExperienceUpdate,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update candidate experience"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update own experience"
            )
        
        # Convert Pydantic model to dict
        experience_dict = experience_data.dict(exclude_unset=True)
        
        experience = await candidate_crud.update_experience(
            db, candidate_id=candidate_id, experience_id=experience_id, experience_data=experience_dict
        )
        return experience
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Update experience error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update experience. Please try again later."
        )

@router.delete("/{candidate_id}/experience/{experience_id}")
async def delete_candidate_experience(
    candidate_id: int,
    experience_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete candidate experience"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete own experience"
            )
        
        await candidate_crud.remove_experience(
            db, candidate_id=candidate_id, experience_id=experience_id
        )
        
        return {"message": "Experience deleted successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the actual error for debugging but return user-friendly message
        print(f"Delete experience error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete experience. Please try again later."
        )

@router.get("/{candidate_id}/applications")
async def get_candidate_applications(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get candidate's applications"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view own applications"
            )
        
        applications = await application_crud.get_by_candidate(
            db, candidate_id=candidate_id, skip=skip, limit=limit
        )
        return applications
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {str(e)}"
        )

@router.get("/{candidate_id}/interactions")
async def get_candidate_interactions(
    candidate_id: int,
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(30, ge=1, le=365)
):
    """Get candidate's interaction history"""
    try:
        if current_user.id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view own interactions"
            )
        
        from services.interaction_service import interaction_service
        interactions = await interaction_service.get_user_interactions(
            db, candidate_id=candidate_id, days_back=days_back
        )
        return interactions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interactions: {str(e)}"
        )