"""
Feedback processing service.
"""
from services.vector_store import VectorStore

class FeedbackService:
    """Service for processing user feedback."""
    
    def __init__(self):
        self.vector_store = VectorStore()
    
    async def process_feedback(self, review_id: str, suggestion_id: str, action: str, reason: str = None, edited_suggestion: str = None):
        """
        Process user feedback on a suggestion.
        
        Args:
            review_id: Review identifier.
            suggestion_id: Suggestion identifier.
            action: Action taken ("accept", "reject", "edit").
            reason: Optional reason for rejection.
            edited_suggestion: Optional edited suggestion text.
        """
        # Store feedback in vector store
        await self.vector_store.store_feedback(
            review_id=review_id,
            suggestion_id=suggestion_id,
            action=action,
            reason=reason,
            edited_suggestion=edited_suggestion
        )


