"""
Evaluation and Benchmark Scoring Harness.
Calculates Accuracy, Precision, Recall, Macro-F1, and Exact Match metrics.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from code.utils.csv_handler import CsvHandler

class AuditEvaluator:
    """Evaluates agent predictions against labeled ground truth data."""

    @staticmethod
    def compute_metrics(
        predictions: List[Dict[str, str]],
        ground_truth: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Compute statistical accuracy, precision, recall, and F1 score.
        
        Args:
            predictions: Rows from predicted output.csv.
            ground_truth: Rows from ground-truth validation dataset.
        Returns:
            Dictionary containing computed evaluation metrics.
        """
        gt_map = {r["request_id"]: r for r in ground_truth if "request_id" in r}
        total = len(predictions)
        if total == 0:
            return {"accuracy": 0.0, "total": 0, "status_matches": 0}

        status_matches = 0
        exact_matches = 0
        per_class_tp: Dict[str, int] = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
        per_class_fp: Dict[str, int] = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
        per_class_fn: Dict[str, int] = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

        for pred in predictions:
            req_id = pred.get("request_id", "")
            if req_id not in gt_map:
                continue

            gt = gt_map[req_id]
            pred_status = pred.get("status", "").strip().upper()
            gt_status = gt.get("status", "").strip().upper()

            if pred_status == gt_status:
                status_matches += 1
                if pred_status in per_class_tp:
                    per_class_tp[pred_status] += 1
            else:
                if pred_status in per_class_fp:
                    per_class_fp[pred_status] += 1
                if gt_status in per_class_fn:
                    per_class_fn[gt_status] += 1

            pred_zombies = set(pred.get("active_zombie_processes", "").split(";")) - {""}
            gt_zombies = set(gt.get("active_zombie_processes", "").split(";")) - {""}

            if pred_status == gt_status and pred_zombies == gt_zombies:
                exact_matches += 1

        accuracy = status_matches / total if total > 0 else 0.0
        exact_match_ratio = exact_matches / total if total > 0 else 0.0

        f1_scores: List[float] = []
        for cls in ["COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"]:
            tp = per_class_tp[cls]
            fp = per_class_fp[cls]
            fn = per_class_fn[cls]
            prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            f1_scores.append(f1)

        macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

        return {
            "total_evaluated": total,
            "status_accuracy": round(accuracy, 4),
            "exact_match_ratio": round(exact_match_ratio, 4),
            "macro_f1": round(macro_f1, 4),
            "per_class_tp": per_class_tp
        }

def main() -> None:
    """CLI entrypoint for running evaluation scorer."""
    parser = argparse.ArgumentParser(description="Evaluate Deletion Audit Predictions")
    parser.add_argument("--predictions", type=str, default="output.csv", help="Path to predictions output.csv")
    parser.add_argument("--ground-truth", type=str, required=True, help="Path to validation_labels.csv")
    args = parser.parse_args()

    preds = CsvHandler.read_csv_safe(Path(args.predictions))
    gt = CsvHandler.read_csv_safe(Path(args.ground_truth))

    metrics = AuditEvaluator.compute_metrics(preds, gt)
    print("=" * 60)
    print("HACKERRANK ORCHESTRATE — AUDIT AGENT EVALUATION METRICS")
    print("=" * 60)
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print("=" * 60)

if __name__ == "__main__":
    main()
