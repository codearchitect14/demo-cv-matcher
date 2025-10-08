from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from config.database import get_db_session
from services.gdpr_service import gdpr_service
from schemas.audit import DataDeletionRequest, ConsentUpdateRequest
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(tags=["GDPR Compliance"])
security = HTTPBearer()

# Simple admin check - in production, use proper JWT authentication
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Get current admin ID from token"""
    # This is a simplified version - in production, decode JWT and verify admin role
    try:
        # For demo purposes, assume token contains admin_id
        admin_id = int(credentials.credentials)
        return admin_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )

@router.delete("/delete_user_data/{candidate_id}")
async def delete_user_data(
    candidate_id: int,
    request: DataDeletionRequest,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete all user data for GDPR compliance.
    
    This endpoint:
    - Deletes candidate profile and all related data
    - Logs the deletion in audit trail
    - Requires admin authentication
    """
    try:
        result = await gdpr_service.delete_user_data(
            db=db,
            candidate_id=candidate_id,
            admin_id=admin_id,
            reason=request.reason,
            request=request
        )
        return {
            "status": "success",
            "message": "User data deleted successfully",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user data: {str(e)}"
        )

@router.put("/update_consent/{candidate_id}")
async def update_consent(
    candidate_id: int,
    request: ConsentUpdateRequest,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update candidate consent status for GDPR compliance.
    
    This endpoint:
    - Updates consent_given field
    - Logs consent changes in audit trail
    - Requires admin authentication
    """
    try:
        result = await gdpr_service.update_consent(
            db=db,
            candidate_id=candidate_id,
            consent_given=request.consent_given,
            admin_id=admin_id,
            request=request
        )
        return {
            "status": "success",
            "message": "Consent updated successfully",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update consent: {str(e)}"
        )

@router.get("/audit_logs/{candidate_id}")
async def get_audit_logs(
    candidate_id: int,
    skip: int = 0,
    limit: int = 100,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get audit logs for a specific user.
    
    This endpoint:
    - Returns audit trail for GDPR compliance
    - Requires admin authentication
    - Supports pagination
    """
    try:
        result = await gdpr_service.get_user_audit_logs(
            db=db,
            candidate_id=candidate_id,
            skip=skip,
            limit=limit
        )
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )

@router.get("/export_user_data/{candidate_id}")
async def export_user_data(
    candidate_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
    request: Request = None
):
    """
    Export user data for GDPR right to data portability.
    
    This endpoint:
    - Exports all user data in structured format
    - Logs the export in audit trail
    - Requires admin authentication
    """
    try:
        result = await gdpr_service.export_user_data(
            db=db,
            candidate_id=candidate_id,
            admin_id=admin_id,
            request=request
        )
        return {
            "status": "success",
            "message": "User data exported successfully",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export user data: {str(e)}"
        )

@router.get("/consent_status/{candidate_id}")
async def get_consent_status(
    candidate_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get consent status for a candidate.
    
    This endpoint:
    - Returns current consent status
    - Requires admin authentication
    """
    try:
        from db.crud.candidate import candidate as candidate_crud
        
        candidate = await candidate_crud.get(db, candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        return {
            "status": "success",
            "data": {
                "candidate_id": candidate_id,
                "consent_given": candidate.consent_given,
                "last_updated": candidate.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consent status: {str(e)}"
        ) 