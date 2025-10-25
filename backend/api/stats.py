"""
API endpoints for learning statistics.
"""
from fastapi import APIRouter, HTTPException
from backend.services.stats_service import StatsService

stats_router = APIRouter()

@stats_router.get("/stats")
async def get_stats():
    """
    Get learning statistics and patterns.
    
    Returns:
        Statistics including acceptance rates, common patterns, etc.
    """
    try:
        stats_service = StatsService()
        stats = await stats_service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

