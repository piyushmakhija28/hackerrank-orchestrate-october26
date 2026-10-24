"""
Zero-Error Submission Packager for HackerRank Orchestrate.
Packages code.zip (excluding datasets and virtualenvs) and verifies all 3 deliverables.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import zipfile
import shutil
import argparse
from pathlib import Path
from typing import Tuple, List

class SubmissionPackager:
    """Packages code and verifies the three required deliverables for HackerRank."""

    EXCLUDED_PATTERNS = {
        "__pycache__",
        ".pyc",
        ".pyo",
        "venv",
        ".venv",
        "node_modules",
        ".git",
        ".idea",
        ".vscode",
        ".DS_Store"
    }

    @classmethod
    def create_code_zip(cls, code_dir: Path, zip_output: Path) -> int:
        """Create a clean zip archive containing only the code/ directory.
        
        Args:
            code_dir: Path to code/ source directory.
            zip_output: Destination path for code.zip.
        Returns:
            Number of files zipped.
        """
        zip_output.parent.mkdir(parents=True, exist_ok=True)
        file_count = 0

        with zipfile.ZipFile(zip_output, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            readme_path = code_dir.parent / "README.md"
            if readme_path.exists():
                zf.write(readme_path, arcname="README.md")
                file_count += 1
            eval_dir = code_dir.parent / "evaluation"
            if eval_dir.exists():
                for ev_file in eval_dir.glob("*.md"):
                    zf.write(ev_file, arcname=f"evaluation/{ev_file.name}")
                    file_count += 1
            for file_path in code_dir.rglob("*"):
                if file_path.is_file():
                    path_str = str(file_path)
                    if any(excluded in path_str for excluded in cls.EXCLUDED_PATTERNS):
                        continue
                    arcname = file_path.relative_to(code_dir.parent)
                    zf.write(file_path, arcname=arcname)
                    file_count += 1
        return file_count

    @classmethod
    def assemble_submission(
        cls,
        code_dir: Path,
        predictions_csv: Path,
        transcript_log: Path,
        submission_dir: Path
    ) -> Tuple[bool, List[str]]:
        """Assemble all 3 deliverables into the submission directory and verify them.
        
        Args:
            code_dir: Path to code directory.
            predictions_csv: Path to output.csv.
            transcript_log: Path to log.txt.
            submission_dir: Destination submission folder.
        Returns:
            Tuple of (all_valid, list_of_status_messages).
        """
        submission_dir.mkdir(parents=True, exist_ok=True)
        messages: List[str] = []

        code_zip_path = submission_dir / "code.zip"
        count = cls.create_code_zip(code_dir, code_zip_path)
        messages.append(f"1. Code Zip: Created {code_zip_path} with {count} files.")

        if predictions_csv.exists():
            dest_csv = submission_dir / "output.csv"
            shutil.copy2(predictions_csv, dest_csv)
            messages.append(f"2. Predictions CSV: Copied to {dest_csv} ({dest_csv.stat().st_size} bytes).")
        else:
            messages.append(f"2. Predictions CSV: MISSING at {predictions_csv}!")

        if transcript_log.exists():
            dest_log = submission_dir / "log.txt"
            shutil.copy2(transcript_log, dest_log)
            messages.append(f"3. Chat Transcript: Copied to {dest_log} ({dest_log.stat().st_size} bytes).")
        else:
            messages.append(f"3. Chat Transcript: MISSING at {transcript_log}!")

        all_present = (
            (submission_dir / "code.zip").exists() and
            (submission_dir / "output.csv").exists() and
            (submission_dir / "log.txt").exists()
        )
        return all_present, messages

def main() -> None:
    """CLI entrypoint for packaging."""
    parser = argparse.ArgumentParser(description="Assemble HackerRank submission files")
    parser.add_argument("--code", type=str, default="code", help="Path to code directory")
    parser.add_argument("--predictions", type=str, default="output.csv", help="Path to output.csv")
    parser.add_argument("--transcript", type=str, default="log.txt", help="Path to log.txt")
    parser.add_argument("--dest", type=str, default="submission", help="Submission output directory")
    args = parser.parse_args()

    success, msgs = SubmissionPackager.assemble_submission(
        Path(args.code),
        Path(args.predictions),
        Path(args.transcript),
        Path(args.dest)
    )
    for m in msgs:
        print(m)
    if success:
        print("\nAll 3 submission deliverables ready in submission/ directory!")
    else:
        print("\nSubmission packaging incomplete. Check missing files above.")

if __name__ == "__main__":
    main()
