"""
Data models for the Code Review Agent.
"""
from pydantic import BaseModel
from typing import List, Optional

class Suggestion(BaseModel):
    """Represents a code review suggestion."""
    id: str
    line_number: int
    end_line_number: Optional[int] = None
    file_path: str
    category: str
    suggestion: str
    confidence: int
    code_snippet: str


