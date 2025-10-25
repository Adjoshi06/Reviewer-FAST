"""
Code review generation service using Ollama and LangChain.
"""
import os
from typing import List, Dict
from datetime import datetime
from langchain_community.llms import Ollama
import json

from backend.services.diff_parser import ParsedDiff, FileChange
from backend.services.vector_store import VectorStore
from backend.models import Suggestion

class ReviewService:
    """Service for generating code reviews using LLM."""
    
    def __init__(self):
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.min_confidence = int(os.getenv("MIN_CONFIDENCE_TO_SHOW", 30))
        
        # Initialize Ollama LLM
        self.llm = Ollama(
            base_url=self.ollama_base_url,
            model=self.model_name,
            temperature=0.3
        )
        
        self.vector_store = VectorStore()
    
    async def generate_review(self, parsed_diff: ParsedDiff, review_id: str) -> List[Suggestion]:
        """
        Generate code review suggestions for a parsed diff.
        
        Args:
            parsed_diff: Parsed diff object.
            review_id: Unique review identifier.
            
        Returns:
            List of review suggestions.
        """
        all_suggestions = []
        
        # Process each file in the diff
        for file_change in parsed_diff.files:
            file_suggestions = await self._review_file(file_change, parsed_diff, review_id)
            all_suggestions.extend(file_suggestions)
        
        # Filter by minimum confidence
        filtered_suggestions = [s for s in all_suggestions if s.confidence >= self.min_confidence]
        
        return filtered_suggestions
    
    async def _review_file(self, file_change: FileChange, parsed_diff: ParsedDiff, review_id: str) -> List[Suggestion]:
        """
        Review a single file's changes.
        
        Args:
            file_change: File change to review.
            parsed_diff: Full parsed diff.
            review_id: Review identifier.
            
        Returns:
            List of suggestions for this file.
        """
        # Build code context
        code_context = self._build_code_context(file_change)
        
        # Get similar past reviews from vector store
        similar_reviews = await self.vector_store.find_similar_code(code_context, limit=3)
        
        # Build prompt with context and learned preferences
        prompt = self._build_review_prompt(code_context, file_change.path, similar_reviews)
        
        # Generate review using LLM
        try:
            response = await self._call_llm(prompt)
            suggestions = self._parse_llm_response(response, file_change.path)
            return suggestions
        except Exception as e:
            print(f"Error generating review for {file_change.path}: {e}")
            return []
    
    def _build_code_context(self, file_change: FileChange) -> str:
        """
        Build code context string from file changes.
        
        Args:
            file_change: File change object.
            
        Returns:
            Code context as string.
        """
        context_lines = []
        for hunk in file_change.hunks:
            for line in hunk["lines"]:
                if line["line_type"] in ["+", "-"]:  # Only changed lines
                    prefix = line["line_type"]
                    line_num = line["target_line_no"] or line["source_line_no"] or 0
                    context_lines.append(f"{prefix} {line_num}: {line['value']}")
        return "\n".join(context_lines)
    
    def _build_review_prompt(self, code_context: str, file_path: str, similar_reviews: List[Dict]) -> str:
        """
        Build prompt for LLM review generation.
        
        Args:
            code_context: Code changes as string.
            file_path: File path being reviewed.
            similar_reviews: Similar past reviews from vector store.
            
        Returns:
            Formatted prompt string.
        """
        # Extract learned preferences from similar reviews
        learned_context = ""
        if similar_reviews:
            accepted_patterns = []
            rejected_patterns = []
            for review in similar_reviews:
                if review.get("action") == "accept":
                    accepted_patterns.append(f"- {review.get('suggestion', '')}")
                elif review.get("action") == "reject":
                    rejected_patterns.append(f"- {review.get('suggestion', '')}")
            
            if accepted_patterns or rejected_patterns:
                learned_context = "\n\n## Learned Preferences:\n"
                if accepted_patterns:
                    learned_context += "User typically accepts:\n" + "\n".join(accepted_patterns[:3]) + "\n"
                if rejected_patterns:
                    learned_context += "User typically rejects:\n" + "\n".join(rejected_patterns[:3]) + "\n"
        
        prompt = f"""You are an expert code reviewer. Analyze the following code changes and provide specific, actionable suggestions.

## File: {file_path}

## Code Changes:
```diff
{code_context}
```

## Review Guidelines:
1. Focus on: bugs, performance issues, security vulnerabilities, best practices, and code clarity
2. Be specific and actionable - suggest concrete improvements
3. Prioritize important issues over style nitpicks
4. Provide confidence scores (0-100) for each suggestion
5. Categorize suggestions: bug, performance, security, best_practice, readability, style
{learned_context}

## Output Format (JSON array):
[
  {{
    "line_number": <int>,
    "end_line_number": <int or null>,
    "category": "<category>",
    "suggestion": "<detailed suggestion>",
    "confidence": <0-100>,
    "code_snippet": "<relevant code snippet>"
  }}
]

Provide only the JSON array, no additional text."""
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call Ollama LLM with prompt.
        
        Args:
            prompt: Review prompt.
            
        Returns:
            LLM response.
        """
        # Run synchronous LLM call in executor
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self.llm.invoke, prompt)
        return response
    
    def _parse_llm_response(self, response: str, file_path: str) -> List[Suggestion]:
        """
        Parse LLM response into Suggestion objects.
        
        Args:
            response: LLM response text.
            file_path: File path for suggestions.
            
        Returns:
            List of Suggestion objects.
        """
        suggestions = []
        
        try:
            # Extract JSON from response (might have markdown code blocks)
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            suggestions_data = json.loads(response)
            
            import uuid
            for sug_data in suggestions_data:
                suggestion = Suggestion(
                    id=str(uuid.uuid4()),
                    line_number=sug_data.get("line_number", 0),
                    end_line_number=sug_data.get("end_line_number"),
                    file_path=file_path,
                    category=sug_data.get("category", "best_practice"),
                    suggestion=sug_data.get("suggestion", ""),
                    confidence=sug_data.get("confidence", 50),
                    code_snippet=sug_data.get("code_snippet", "")
                )
                suggestions.append(suggestion)
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response: {response[:500]}")
        except Exception as e:
            print(f"Error creating suggestions: {e}")
        
        return suggestions
    
    async def store_review_session(self, review_id: str, parsed_diff: ParsedDiff, suggestions: List[Suggestion]):
        """
        Store review session in vector store.
        
        Args:
            review_id: Review identifier.
            parsed_diff: Parsed diff.
            suggestions: List of suggestions.
        """
        # Store each file's context with review metadata
        for file_change in parsed_diff.files:
            code_context = self._build_code_context(file_change)
            file_suggestions = [s for s in suggestions if s.file_path == file_change.path]
            
            await self.vector_store.store_review_context(
                review_id=review_id,
                file_path=file_change.path,
                code_context=code_context,
                suggestions=file_suggestions
            )
    
    async def get_recent_reviews(self, limit: int = 10) -> List[Dict]:
        """
        Get recent reviews.
        
        Args:
            limit: Maximum number of reviews.
            
        Returns:
            List of review summaries.
        """
        return await self.vector_store.get_recent_reviews(limit)
    
    async def get_review(self, review_id: str) -> Dict:
        """
        Get a specific review by ID.
        
        Args:
            review_id: Review identifier.
            
        Returns:
            Review details.
        """
        return await self.vector_store.get_review(review_id)

