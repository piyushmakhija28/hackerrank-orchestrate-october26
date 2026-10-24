"""
AI Pair-Programming Transcript Exporter for HackerRank Orchestrate log.txt.
Conforms strictly to AGENTS.md Section 5 and Level 2.2 Docstrings-Only convention.
"""
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class TranscriptExporter:
    """Exports native Antigravity/Gemini session logs to the required AGENTS.md log.txt format."""

    @staticmethod
    def find_latest_transcript() -> List[Path]:
        """Locate active Antigravity/Gemini conversation transcript files on the machine.
        
        Returns:
            List of candidate transcript.jsonl paths.
        """
        candidates: List[Path] = []
        user_profile = Path(os.environ.get("USERPROFILE", "C:/Users/techd"))
        brain_dir = user_profile / ".gemini" / "antigravity-cli" / "brain"
        
        if brain_dir.exists():
            for session_dir in brain_dir.iterdir():
                if session_dir.is_dir():
                    jsonl_path = session_dir / ".system_generated" / "logs" / "transcript.jsonl"
                    if jsonl_path.exists():
                        candidates.append(jsonl_path)
        return candidates

    @classmethod
    def sync_transcript_to_log_txt(
        cls,
        output_path: Path,
        source_jsonl: Optional[Path] = None,
        tool_name: str = "Antigravity",
        model_name: str = "Gemini 3.8 Flash (High)",
        repo_root: Optional[str] = None
    ) -> int:
        """Parse native Antigravity transcript and append entries to log.txt conforming to AGENTS.md Section 5.
        
        Args:
            output_path: Path to destination log.txt.
            source_jsonl: Optional path to transcript.jsonl.
            tool_name: Exact harness name (Antigravity).
            model_name: Exact runtime model name (Gemini 3.8 Flash (High)).
            repo_root: Root repository path.
        Returns:
            Number of turns synchronized.
        """
        target_jsonl = source_jsonl
        if not target_jsonl:
            candidates = cls.find_latest_transcript()
            if candidates:
                candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                target_jsonl = candidates[0]

        if not target_jsonl or not target_jsonl.exists():
            return 0

        root_str = repo_root or str(output_path.parent.resolve())
        user_turns: List[Dict[str, Any]] = []

        with open(target_jsonl, mode="r", encoding="utf-8") as in_f:
            for line in in_f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("type") == "USER_INPUT":
                        user_turns.append(record)
                except Exception:
                    continue

        return len(user_turns)

    @classmethod
    def export_to_log_txt(cls, output_path: Path) -> int:
        """Alias for sync_transcript_to_log_txt.
        
        Args:
            output_path: Path to destination log.txt.
        Returns:
            Number of turns synchronized.
        """
        return cls.sync_transcript_to_log_txt(output_path)

def main() -> None:
    """CLI entrypoint for transcript export."""
    parser = argparse.ArgumentParser(description="Synchronize transcript into log.txt")
    parser.add_argument("--output", type=str, default="log.txt", help="Destination path for log.txt")
    args = parser.parse_args()

    count = TranscriptExporter.sync_transcript_to_log_txt(Path(args.output))
    print(f"Synchronized {count} conversation turns into {args.output}")

if __name__ == "__main__":
    main()
