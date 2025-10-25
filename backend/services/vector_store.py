"""
Vector store service using ChromaDB for learning memory.
"""
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from datetime import datetime
import json

class VectorStore:
    """Vector store for storing and retrieving review feedback."""
    
    def __init__(self):
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        
        # Collection for code patterns and suggestions
        self.suggestions_collection = self.client.get_or_create_collection(
            name="suggestions",
            metadata={"description": "Code review suggestions with feedback"}
        )
        
        # Collection for review sessions
        self.reviews_collection = self.client.get_or_create_collection(
            name="reviews",
            metadata={"description": "Review sessions"}
        )
    
    async def find_similar_code(self, code_context: str, limit: int = 3) -> List[Dict]:
        """
        Find similar code patterns from past reviews.
        
        Args:
            code_context: Code context to search for.
            limit: Maximum number of results.
            
        Returns:
            List of similar review entries.
        """
        try:
            # Query for similar code patterns
            # Get all items first, then filter by action
            try:
                results = self.suggestions_collection.query(
                    query_texts=[code_context],
                    n_results=min(limit * 3, 20)  # Get more results to filter
                )
            except Exception as e:
                print(f"ChromaDB query error: {e}")
                return []
            
            similar_reviews = []
            if results.get("documents") and len(results["documents"]) > 0 and len(results["documents"][0]) > 0:
                metadatas = results.get("metadatas", [])
                if not metadatas:
                    metadatas = [[]]
                
                for i in range(len(results["documents"][0])):
                    doc = results["documents"][0][i]
                    metadata = metadatas[0][i] if i < len(metadatas[0]) else {}
                    
                    # Only include items with feedback (accept/reject)
                    action = metadata.get("action", "pending")
                    if action in ["accept", "reject", "edit"]:
                        similar_reviews.append({
                            "code_context": doc,
                            "suggestion": metadata.get("suggestion", ""),
                            "action": action,
                            "reason": metadata.get("reason", ""),
                            "category": metadata.get("category", ""),
                            "confidence": metadata.get("confidence", 0)
                        })
                    
                    # Stop when we have enough filtered results
                    if len(similar_reviews) >= limit:
                        break
            
            return similar_reviews
        except Exception as e:
            print(f"Error finding similar code: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def store_review_context(self, review_id: str, file_path: str, code_context: str, suggestions: List):
        """
        Store review context in vector store.
        
        Args:
            review_id: Review identifier.
            file_path: File path.
            code_context: Code context string.
            suggestions: List of suggestions.
        """
        try:
            # Store each suggestion as a document (will be updated with feedback later)
            import uuid
            for suggestion in suggestions:
                doc_id = f"{review_id}_{file_path}_{suggestion.id}"
                
                self.suggestions_collection.add(
                    documents=[code_context],
                    ids=[doc_id],
                    metadatas=[{
                        "review_id": review_id,
                        "file_path": file_path,
                        "suggestion_id": suggestion.id,
                        "suggestion": suggestion.suggestion,
                        "category": suggestion.category,
                        "confidence": suggestion.confidence,
                        "line_number": suggestion.line_number,
                        "action": "pending",  # Will be updated when feedback is given
                        "timestamp": datetime.utcnow().isoformat()
                    }]
                )
        except Exception as e:
            print(f"Error storing review context: {e}")
    
    async def store_feedback(self, review_id: str, suggestion_id: str, action: str, reason: Optional[str] = None, edited_suggestion: Optional[str] = None):
        """
        Store feedback on a suggestion.
        
        Args:
            review_id: Review identifier.
            suggestion_id: Suggestion identifier.
            action: Action taken ("accept", "reject", "edit").
            reason: Optional reason for rejection.
            edited_suggestion: Optional edited suggestion text.
        """
        try:
            # Find the suggestion document
            results = self.suggestions_collection.get(
                where={"review_id": review_id, "suggestion_id": suggestion_id}
            )
            
            if results["ids"]:
                doc_id = results["ids"][0]
                metadata = results["metadatas"][0] if results["metadatas"] else {}
                
                # Update metadata with feedback
                updated_metadata = metadata.copy()
                updated_metadata["action"] = action
                updated_metadata["reason"] = reason or ""
                updated_metadata["feedback_timestamp"] = datetime.utcnow().isoformat()
                
                if edited_suggestion:
                    updated_metadata["edited_suggestion"] = edited_suggestion
                    updated_metadata["suggestion"] = edited_suggestion
                
                # Update the document
                self.suggestions_collection.update(
                    ids=[doc_id],
                    metadatas=[updated_metadata]
                )
            else:
                print(f"Warning: Suggestion {suggestion_id} not found in vector store")
        except Exception as e:
            print(f"Error storing feedback: {e}")
    
    async def get_recent_reviews(self, limit: int = 10) -> List[Dict]:
        """
        Get recent review sessions.
        
        Args:
            limit: Maximum number of reviews.
            
        Returns:
            List of review summaries.
        """
        try:
            # Get all reviews from suggestions collection, grouped by review_id
            all_results = self.suggestions_collection.get()
            
            review_ids = set()
            for metadata in all_results.get("metadatas", []):
                if "review_id" in metadata:
                    review_ids.add(metadata["review_id"])
            
            reviews = []
            for review_id in list(review_ids)[:limit]:
                review = await self.get_review(review_id)
                if review:
                    reviews.append(review)
            
            # Sort by timestamp (most recent first)
            reviews.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return reviews
        except Exception as e:
            print(f"Error getting recent reviews: {e}")
            return []
    
    async def get_review(self, review_id: str) -> Optional[Dict]:
        """
        Get a specific review by ID.
        
        Args:
            review_id: Review identifier.
            
        Returns:
            Review details or None.
        """
        try:
            results = self.suggestions_collection.get(
                where={"review_id": review_id}
            )
            
            if not results["ids"]:
                return None
            
            # Group suggestions by file
            files = {}
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                file_path = metadata.get("file_path", "unknown")
                
                if file_path not in files:
                    files[file_path] = {
                        "file_path": file_path,
                        "suggestions": []
                    }
                
                files[file_path]["suggestions"].append({
                    "id": metadata.get("suggestion_id", ""),
                    "line_number": metadata.get("line_number", 0),
                    "category": metadata.get("category", ""),
                    "suggestion": metadata.get("suggestion", ""),
                    "confidence": metadata.get("confidence", 0),
                    "action": metadata.get("action", "pending")
                })
            
            # Get earliest timestamp for this review
            timestamps = [m.get("timestamp", "") for m in results.get("metadatas", []) if m.get("timestamp")]
            created_at = min(timestamps) if timestamps else datetime.utcnow().isoformat()
            
            return {
                "review_id": review_id,
                "files": list(files.values()),
                "created_at": created_at,
                "suggestion_count": len(results["ids"])
            }
        except Exception as e:
            print(f"Error getting review: {e}")
            return None

