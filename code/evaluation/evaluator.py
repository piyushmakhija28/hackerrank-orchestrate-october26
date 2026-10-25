"""Evaluation and benchmark scoring harness for deletion audits.

Calculates case-level status accuracy, step-level precision, recall, sequence order compliance,
field-level matching, and macro-F1 metrics conforming strictly to Level 2.2 Docstrings-Only convention.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.utils.csv_handler import CsvHandler


class AuditEvaluator:
    """Evaluates agent deletion audit predictions against labeled ground-truth datasets."""

    @staticmethod
    def parse_steps_safe(steps_str: str) -> List[Dict[str, Any]]:
        """Parses a serialized JSON array of audit steps into structured dictionaries.

        Args:
            steps_str: Raw JSON string from output CSV steps_json column.
        Returns:
            List of parsed step dictionaries, or empty list if unparseable.
        """
        if not steps_str or not steps_str.strip():
            return []
        try:
            parsed = json.loads(steps_str)
            if isinstance(parsed, list):
                return parsed
            return []
        except Exception:
            return []

    @classmethod
    def compute_metrics(
        cls,
        predictions: List[Dict[str, str]],
        ground_truth: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Calculates comprehensive case, step, field, and sequence evaluation metrics.

        Args:
            predictions: Predicted rows from agent output.csv.
            ground_truth: Ground-truth validation rows (e.g. sample_output.csv).
        Returns:
            Dictionary containing evaluated statistical metrics and scores.
        """
        def get_case_id(r: Dict[str, str]) -> str:
            return r.get("case_id") or r.get("request_id") or ""

        def get_status(r: Dict[str, str]) -> str:
            return (r.get("deletion_status") or r.get("status") or "").strip().upper()

        gt_map = {get_case_id(r): r for r in ground_truth if get_case_id(r)}
        pred_map = {get_case_id(r): r for r in predictions if get_case_id(r)}
        common_cids = [cid for cid in pred_map if cid in gt_map]
        total = len(common_cids)

        if total == 0:
            return {
                "total_evaluated": 0,
                "status_accuracy": 0.0,
                "exact_match_ratio": 0.0,
                "macro_f1": 0.0,
                "step_count_accuracy": 0.0,
                "sequence_order_accuracy": 0.0,
                "field_level_accuracy": 0.0,
                "overlap_warning": True,
                "warning_message": f"Zero overlapping case_ids between predictions ({len(predictions)}) and ground_truth ({len(ground_truth)}). Check case_id alignment.",
                "per_class_metrics": {},
            }

        status_matches = 0
        exact_matches = 0
        step_count_matches = 0
        valid_sequences = 0
        phase_ranks = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}

        per_class_tp: Dict[str, int] = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
        per_class_fp: Dict[str, int] = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
        per_class_fn: Dict[str, int] = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

        total_fields_matched = 0
        total_fields_expected = 0

        for cid in common_cids:
            pred = pred_map[cid]
            gt = gt_map[cid]
            pred_status = get_status(pred)
            gt_status = get_status(gt)

            if pred_status == gt_status:
                status_matches += 1
                if pred_status in per_class_tp:
                    per_class_tp[pred_status] += 1
            else:
                if pred_status in per_class_fp:
                    per_class_fp[pred_status] += 1
                if gt_status in per_class_fn:
                    per_class_fn[gt_status] += 1

            pred_steps = cls.parse_steps_safe(pred.get("steps_json", ""))
            gt_steps = cls.parse_steps_safe(gt.get("steps_json", ""))

            if len(pred_steps) == len(gt_steps):
                step_count_matches += 1

            is_seq_valid = True
            last_p_rank = 0
            for idx, st in enumerate(pred_steps, start=1):
                if st.get("step_no") != idx:
                    is_seq_valid = False
                    break
                p_rank = phase_ranks.get(st.get("phase", ""), 99)
                if p_rank < last_p_rank:
                    is_seq_valid = False
                    break
                last_p_rank = p_rank
            if is_seq_valid:
                valid_sequences += 1

            fields_matched = 0
            fields_expected = len(gt_steps) * 6
            for p_step, g_step in zip(pred_steps, gt_steps):
                for k in ["phase", "system_id", "resource_id", "operation", "state", "evidence_id"]:
                    if p_step.get(k) == g_step.get(k):
                        fields_matched += 1
            total_fields_matched += fields_matched
            total_fields_expected += fields_expected

            steps_identical = False
            if pred_status == gt_status:
                if len(pred_steps) == len(gt_steps):
                    all_match = True
                    for p_s, g_s in zip(pred_steps, gt_steps):
                        for k in ["phase", "system_id", "resource_id", "operation", "state", "evidence_id"]:
                            if p_s.get(k) != g_s.get(k):
                                all_match = False
                                break
                        if not all_match:
                            break
                    steps_identical = all_match
            if steps_identical:
                exact_matches += 1

        accuracy = status_matches / total if total > 0 else 0.0
        exact_ratio = exact_matches / total if total > 0 else 0.0
        step_acc = step_count_matches / total if total > 0 else 0.0
        seq_acc = valid_sequences / total if total > 0 else 0.0
        field_acc = total_fields_matched / total_fields_expected if total_fields_expected > 0 else 1.0

        f1_scores: List[float] = []
        per_class_summary: Dict[str, Dict[str, float]] = {}
        for cls_name in ["COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"]:
            tp = per_class_tp[cls_name]
            fp = per_class_fp[cls_name]
            fn = per_class_fn[cls_name]
            prec = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
            rec = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if fp == 0 else 0.0)
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            f1_scores.append(f1)
            per_class_summary[cls_name] = {
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
                "support": tp + fn,
            }

        macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

        return {
            "total_evaluated": total,
            "status_accuracy": round(accuracy, 4),
            "exact_match_ratio": round(exact_ratio, 4),
            "step_count_accuracy": round(step_acc, 4),
            "sequence_order_accuracy": round(seq_acc, 4),
            "field_level_accuracy": round(field_acc, 4),
            "macro_f1": round(macro_f1, 4),
            "overlap_warning": False,
            "per_class_metrics": per_class_summary,
        }


def main() -> None:
    """CLI entrypoint for running the deletion audit evaluation scorer."""
    parser = argparse.ArgumentParser(description="Evaluate Deletion Audit Predictions against Ground Truth")
    parser.add_argument("--predictions", type=str, default="output.csv", help="Path to predictions output.csv")
    parser.add_argument("--ground-truth", type=str, default="dataset/sample_output.csv", help="Path to ground truth CSV")
    args = parser.parse_args()

    preds = CsvHandler.read_csv_safe(Path(args.predictions))
    gt = CsvHandler.read_csv_safe(Path(args.ground_truth))

    metrics = AuditEvaluator.compute_metrics(preds, gt)
    print("=" * 70)
    print("HACKERRANK ORCHESTRATE — DELETION AUDIT EVALUATION SCORECARD")
    print("=" * 70)
    if metrics.get("overlap_warning"):
        print(f"WARNING: {metrics.get('warning_message')}")
        print("=" * 70)
        return

    print(f"Total Cases Evaluated   : {metrics['total_evaluated']}")
    print(f"Case Status Accuracy    : {metrics['status_accuracy'] * 100:.2f}%")
    print(f"Step Count Accuracy     : {metrics['step_count_accuracy'] * 100:.2f}%")
    print(f"Sequence Order Accuracy : {metrics['sequence_order_accuracy'] * 100:.2f}%")
    print(f"Field-Level Accuracy    : {metrics['field_level_accuracy'] * 100:.2f}%")
    print(f"Exact Match Ratio       : {metrics['exact_match_ratio'] * 100:.2f}%")
    print(f"Macro-F1 Score          : {metrics['macro_f1']:.4f}")
    print("-" * 70)
    print("Per-Class Performance Breakdown:")
    for cls_name, stats in metrics.get("per_class_metrics", {}).items():
        print(f"  [{cls_name:<14}] Precision: {stats['precision']:.4f} | Recall: {stats['recall']:.4f} | F1: {stats['f1']:.4f} | Support: {stats['support']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
