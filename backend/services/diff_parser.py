"""
Diff parser for extracting code changes.
"""
from unidiff import PatchSet
from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class FileChange:
    """Represents changes in a single file."""
    path: str
    additions: int
    deletions: int
    hunks: List[Dict]  # List of hunk dictionaries with line info

@dataclass
class ParsedDiff:
    """Represents a parsed diff."""
    files: List[FileChange]
    raw_content: str

class DiffParser:
    """Parser for git diff content."""
    
    def parse(self, diff_content: str) -> ParsedDiff:
        """
        Parse diff content into structured format.
        
        Args:
            diff_content: Raw diff content.
            
        Returns:
            ParsedDiff object with file changes.
        """
        patch_set = PatchSet(diff_content)
        files = []
        
        for patched_file in patch_set:
            # Skip deleted files
            if patched_file.is_removed_file:
                continue
            
            hunks = []
            for hunk in patched_file:
                hunk_data = {
                    "source_start": hunk.source_start,
                    "source_length": hunk.source_length,
                    "target_start": hunk.target_start,
                    "target_length": hunk.target_length,
                    "lines": []
                }
                
                for line in hunk:
                    hunk_data["lines"].append({
                        "line_type": str(line.line_type),  # '+', '-', or ' '
                        "value": line.value,
                        "source_line_no": line.source_line_no,
                        "target_line_no": line.target_line_no
                    })
                
                hunks.append(hunk_data)
            
            file_change = FileChange(
                path=patched_file.path,
                additions=patched_file.added,
                deletions=patched_file.removed,
                hunks=hunks
            )
            files.append(file_change)
        
        return ParsedDiff(files=files, raw_content=diff_content)
    
    def get_file_context(self, diff: ParsedDiff, file_path: str, line_number: int, context_lines: int = 5) -> str:
        """
        Get code context around a specific line.
        
        Args:
            diff: Parsed diff object.
            file_path: File path to get context from.
            line_number: Line number to get context around.
            context_lines: Number of context lines before and after.
            
        Returns:
            Code context as string.
        """
        for file_change in diff.files:
            if file_change.path == file_path:
                context = []
                for hunk in file_change.hunks:
                    for line in hunk["lines"]:
                        if line["target_line_no"] and abs(line["target_line_no"] - line_number) <= context_lines:
                            context.append(f"{line['target_line_no']}: {line['value']}")
                return "\n".join(context)
        return ""


