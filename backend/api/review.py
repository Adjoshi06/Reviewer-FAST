"""
API endpoints for code review operations.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

from backend.services.github_service import GitHubService
from backend.services.review_service import ReviewService
from backend.services.diff_parser import DiffParser
from backend.models import Suggestion

review_router = APIRouter()

class ReviewRequest(BaseModel):
    source: str  # "github" or "diff"
    url: Optional[str] = None  # GitHub PR URL
    content: Optional[str] = None  # Direct diff content
    pr_number: Optional[int] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None

class ReviewResponse(BaseModel):
    review_id: str
    suggestions: List[Suggestion]
    file_count: int
    total_changes: int
    created_at: str

@review_router.post("/review", response_model=ReviewResponse)
async def create_review(request: ReviewRequest):
    """
    Create a code review from GitHub PR or diff content.
    
    Args:
        request: Review request with source type and content.
        
    Returns:
        Review response with suggestions.
    """
    try:
        review_id = str(uuid.uuid4())
        diff_content = None
        file_path = None
        
        # Get diff content
        if request.source == "github":
            if not request.url and not (request.repo_owner and request.repo_name and request.pr_number):
                raise HTTPException(status_code=400, detail="GitHub URL or repo details required")
            
            github_service = GitHubService()
            if request.url:
                diff_content, file_path = await github_service.fetch_pr_diff(request.url)
            else:
                diff_content, file_path = await github_service.fetch_pr_diff_by_repo(
                    request.repo_owner, request.repo_name, request.pr_number
                )
        elif request.source == "diff":
            if not request.content:
                raise HTTPException(status_code=400, detail="Diff content required")
            diff_content = request.content
            file_path = "unknown"
        else:
            raise HTTPException(status_code=400, detail="Invalid source type")
        
        # Parse diff
        diff_parser = DiffParser()
        parsed_diff = diff_parser.parse(diff_content)
        
        # Generate review
        review_service = ReviewService()
        suggestions = await review_service.generate_review(parsed_diff, review_id)
        
        # Store review session
        await review_service.store_review_session(review_id, parsed_diff, suggestions)
        
        return ReviewResponse(
            review_id=review_id,
            suggestions=suggestions,
            file_count=len(parsed_diff.files),
            total_changes=sum(f.additions + f.deletions for f in parsed_diff.files),
            created_at=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@review_router.get("/reviews")
async def get_reviews(limit: int = 10):
    """
    Get list of recent reviews.
    
    Args:
        limit: Maximum number of reviews to return.
        
    Returns:
        List of review summaries.
    """
    try:
        review_service = ReviewService()
        reviews = await review_service.get_recent_reviews(limit)
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@review_router.get("/review/{review_id}")
async def get_review(review_id: str):
    """
    Get a specific review by ID.
    
    Args:
        review_id: Review identifier.
        
    Returns:
        Review details with suggestions.
    """
    try:
        review_service = ReviewService()
        review = await review_service.get_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

