from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.email_service import email_service

router = APIRouter(tags=["Email Test"])

class EmailTestRequest(BaseModel):
    email: str
    name: str

@router.post("/test-email")
async def test_email_delivery(request: EmailTestRequest):
    """Test email delivery to a specific address"""
    try:
        print(f"🧪 Testing email delivery to: {request.email}")
        
        success = await email_service.send_welcome_email(
            candidate_email=request.email,
            candidate_name=request.name
        )
        
        if success:
            return {
                "message": f"Test email sent successfully to {request.email}",
                "success": True,
                "email": request.email
            }
        else:
            return {
                "message": f"Failed to send test email to {request.email}",
                "success": False,
                "email": request.email
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email test failed: {str(e)}"
        )
