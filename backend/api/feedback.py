"""
API endpoints for feedback collection.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.services.feedback_service import FeedbackService

feedback_router = APIRouter()

class FeedbackRequest(BaseModel):
    review_id: str
    suggestion_id: str
    action: str  # "accept", "reject", "edit"
    reason: Optional[str] = None
    edited_suggestion: Optional[str] = None

class FeedbackResponse(BaseModel):
    success: bool
    message: str

@feedback_router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback on a code review suggestion.
    
    Args:
        request: Feedback request with action and optional reason.
        
    Returns:
        Success response.
    """
    try:
        if request.action not in ["accept", "reject", "edit"]:
            raise HTTPException(status_code=400, detail="Invalid action. Must be 'accept', 'reject', or 'edit'")
        
        feedback_service = FeedbackService()
        await feedback_service.process_feedback(
            review_id=request.review_id,
            suggestion_id=request.suggestion_id,
            action=request.action,
            reason=request.reason,
            edited_suggestion=request.edited_suggestion
        )
        
        return FeedbackResponse(
            success=True,
            message=f"Feedback {request.action}ed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

