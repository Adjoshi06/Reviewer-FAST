"""
Statistics service for learning analytics.
"""
from backend.services.vector_store import VectorStore
from typing import Dict
from collections import defaultdict

class StatsService:
    """Service for generating learning statistics."""
    
    def __init__(self):
        self.vector_store = VectorStore()
    
    async def get_statistics(self) -> Dict:
        """
        Get learning statistics and patterns.
        
        Returns:
            Dictionary with statistics.
        """
        try:
            # Get all suggestions
            all_results = self.vector_store.suggestions_collection.get()
            
            # Filter to only those with feedback
            feedback_items = []
            for i, doc_id in enumerate(all_results.get("ids", [])):
                metadata = all_results.get("metadatas", [{}])[i] if i < len(all_results.get("metadatas", [])) else {}
                action = metadata.get("action", "pending")
                if action in ["accept", "reject", "edit"]:
                    feedback_items.append(metadata)
            
            if not feedback_items:
                return {
                    "total_feedback": 0,
                    "acceptance_rate": 0,
                    "by_category": {},
                    "by_confidence": {},
                    "recent_patterns": []
                }
            
            # Calculate statistics
            total_feedback = len(feedback_items)
            accepts = 0
            rejects = 0
            edits = 0
            
            by_category = defaultdict(lambda: {"accept": 0, "reject": 0, "edit": 0})
            by_confidence_range = defaultdict(lambda: {"accept": 0, "reject": 0})
            
            for metadata in feedback_items:
                action = metadata.get("action", "")
                category = metadata.get("category", "unknown")
                confidence = metadata.get("confidence", 50)
                
                if action == "accept":
                    accepts += 1
                    by_category[category]["accept"] += 1
                elif action == "reject":
                    rejects += 1
                    by_category[category]["reject"] += 1
                elif action == "edit":
                    edits += 1
                    by_category[category]["edit"] += 1
                
                # Group by confidence ranges
                confidence_range = f"{(confidence // 20) * 20}-{(confidence // 20) * 20 + 19}"
                if action in ["accept", "reject"]:
                    by_confidence_range[confidence_range][action] += 1
            
            acceptance_rate = (accepts / total_feedback * 100) if total_feedback > 0 else 0
            
            # Get recent patterns (last 10 feedback items, sorted by timestamp)
            recent_patterns = []
            sorted_items = sorted(
                feedback_items,
                key=lambda x: x.get("feedback_timestamp", x.get("timestamp", "")),
                reverse=True
            )[:10]
            
            for metadata in sorted_items:
                recent_patterns.append({
                    "category": metadata.get("category", ""),
                    "action": metadata.get("action", ""),
                    "confidence": metadata.get("confidence", 0),
                    "timestamp": metadata.get("feedback_timestamp", metadata.get("timestamp", ""))
                })
            
            return {
                "total_feedback": total_feedback,
                "acceptance_rate": round(acceptance_rate, 2),
                "accepts": accepts,
                "rejects": rejects,
                "edits": edits,
                "by_category": dict(by_category),
                "by_confidence": dict(by_confidence_range),
                "recent_patterns": recent_patterns
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                "error": str(e),
                "total_feedback": 0,
                "acceptance_rate": 0
            }

