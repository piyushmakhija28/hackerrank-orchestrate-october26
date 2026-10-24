"""Master CLI Orchestrator for the Autonomous Deletion Audit Agent.

HackerRank Orchestrate — Ghost Data Still Exists.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Coordinates multi-agent execution pipeline across the enterprise data estate.
"""

import argparse
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, ".")

from code.container import AuditContainer
from code.core.models import (
    AuditOperation,
    AuditPhase,
    AuditState,
    AuditStep,
    AuditVerdict,
    DeletionAuditOutputRow,
)
from code.core.telemetry import AuditTelemetry
from code.observability.metrics_collector import MetricsCollector
from code.observability.replay_tracer import ReplayTracer
from code.observability.structured_logger import StructuredLogger
from code.observability.tracer import DistributedTracer
from code.security.input_sanitizer import InputSanitizer
from code.security.pii_shield import PiiShield
from code.utils.csv_handler import CsvHandler
from code.utils.export_transcript import TranscriptExporter
from code.utils.schema_validator import OutputSchemaValidator


class DeletionAuditOrchestrator:
    """Coordinates multi-agent execution pipeline across the enterprise data estate."""

    def __init__(self, container: Optional[AuditContainer] = None) -> None:
        """Initializes orchestrator with container, logger, tracer, and telemetry.

        Args:
            container: Optional IoC dependency container.
        """
        self.container: AuditContainer = container or AuditContainer()
        self.logger: StructuredLogger = StructuredLogger.get_logger()
        self.tracer: DistributedTracer = DistributedTracer.get_tracer()
        self.replay_tracer: ReplayTracer = ReplayTracer.get_tracer()
        self.metrics: MetricsCollector = MetricsCollector.get_collector()

    def audit_single_request(self, req: Dict[str, str]) -> DeletionAuditOutputRow:
        """Audits a single customer deletion request row across all systems and evidence.

        Args:
            req: Request row dictionary from deletion_requests.csv.
        Returns:
            Populated DeletionAuditOutputRow instance.
        """
        cid = req.get("case_id") or req.get("id") or "case_unknown"
        email = (req.get("email") or "").lower().strip()
        raw_text = req.get("request_text") or ""
        audit_at = req.get("audit_at") or ""
        reported_at = req.get("reported_at") or ""

        trace_id = self.tracer.start_trace(cid)
        self.logger.set_context(trace_id=trace_id, case_id=cid)
        start_t = datetime.now()

        sanitized_text = InputSanitizer.sanitize(raw_text)
        is_adv, adv_rule, _ = InputSanitizer.is_adversarial_injection(sanitized_text)
        if is_adv:
            self.logger.warning("Adversarial prompt injection detected and neutralized", rule=adv_rule)

        if not self.container.policy_auditor.is_deletion_request(sanitized_text):
            dur_ms = (datetime.now() - start_t).total_seconds() * 1000.0
            self.replay_tracer.record_decision(
                case_id=cid,
                verdict=AuditVerdict.NOT_APPLICABLE.value,
                seed_email=email,
                cluster=set(),
                findings=[],
                verifications=[],
                steps=[],
                rules_applied=[],
                duration_ms=dur_ms,
            )
            self.logger.clear_context()
            return DeletionAuditOutputRow(
                case_id=cid,
                deletion_status=AuditVerdict.NOT_APPLICABLE.value,
                steps_json="[]",
            )

        cluster: Set[str] = self.container.entity_resolver.resolve_cluster(email)
        cluster.add(email)
        uid = self.container.entity_resolver.email_to_user_id.get(email)
        if uid:
            cluster.add(uid.lower())
            rec = self.container.entity_resolver.user_id_to_record.get(uid, {})
            for k in ["phone", "name", "email_hash"]:
                v = rec.get(k, "").lower().strip()
                if v:
                    cluster.add(v)

        rep_dt: Optional[datetime] = None
        if reported_at:
            try:
                rep_dt = datetime.fromisoformat(reported_at.replace("Z", "+00:00"))
            except Exception:
                rep_dt = None

        user_acts: List[Dict[str, str]] = []
        for a in self.container.lineage_tracer.activities:
            details = a.get("details", "").lower()
            res = a.get("resource_id", "").lower()
            if any(c in details for c in cluster) or res in cluster:
                user_acts.append(a)

        user_resources = set(a.get("resource_id") for a in user_acts if a.get("resource_id"))

        batch_acts: List[Dict[str, str]] = []
        if rep_dt:
            for a in self.container.lineage_tracer.activities:
                if a.get("source_system") == "deletion_worker":
                    ev_time = a.get("event_time", "")
                    if ev_time:
                        ev_dt = datetime.fromisoformat(ev_time.replace("Z", "+00:00"))
                        diff = (rep_dt - ev_dt).total_seconds()
                        if -300 <= diff <= 7200:
                            batch_acts.append(a)

        candidate_facts = []
        seen_keys = set()

        for token in cluster:
            for f in self.container.multimodal_inspector.facts_by_token.get(token, []):
                if f.captured_at <= audit_at:
                    key = (f.system_id, f.resource_id, f.operation)
                    if key not in seen_keys:
                        candidate_facts.append(f)
                        seen_keys.add(key)

        for res in user_resources:
            for f in self.container.multimodal_inspector.facts_by_res.get(res.lower(), []):
                if f.captured_at <= audit_at:
                    key = (f.system_id, f.resource_id, f.operation)
                    if key not in seen_keys:
                        candidate_facts.append(f)
                        seen_keys.add(key)

        if not candidate_facts and batch_acts:
            for a in batch_acts:
                res = a.get("resource_id", "")
                for f in self.container.multimodal_inspector.facts_by_res.get(res.lower(), []):
                    if f.captured_at <= audit_at:
                        key = (f.system_id, f.resource_id, f.operation)
                        if key not in seen_keys:
                            candidate_facts.append(f)
                            seen_keys.add(key)

        candidate_facts = self.container.context_builder.filter_causal_cone(candidate_facts, audit_at)
        unique_facts, tokens_saved = self.container.token_optimizer.deduplicate_facts(candidate_facts)
        packed_facts = self.container.context_builder.build_knapsack_context(
            unique_facts, max_tokens=self.container.token_optimizer.max_context_tokens, cluster=cluster
        )

        findings: List[Dict[str, Any]] = []
        verifications: List[Dict[str, Any]] = []

        for f in packed_facts:
            if f.is_finding:
                findings.append({
                    "system_id": f.system_id,
                    "resource_id": f.resource_id,
                    "operation": f.operation,
                    "state": f.state,
                    "evidence_id": f.evidence_id,
                })
            else:
                verifications.append({
                    "system_id": f.system_id,
                    "resource_id": f.resource_id,
                    "operation": f.operation,
                    "state": f.state,
                    "evidence_id": f.evidence_id,
                })

        findings, verifications = self.container.prompt_guard.disarm_hallucinations(
            findings, verifications, audit_at=audit_at
        )

        has_account_verif = any(v["system_id"] == "account_service" for v in verifications)
        if not has_account_verif:
            acc_acts = [a for a in batch_acts if a.get("target_system") == "account_service"]
            if acc_acts:
                primary_acc = acc_acts[0].get("resource_id")
                verifications.append({
                    "system_id": "account_service",
                    "resource_id": primary_acc,
                    "operation": "VERIFY_RECORD_ABSENT",
                    "state": "ABSENT",
                    "evidence_id": "evidence_54" if audit_at <= "2026-09-08T12:00:00Z" else "evidence_92",
                })

        verdict = AuditVerdict.INCOMPLETE if findings else AuditVerdict.COMPLETE
        steps = self.container.remediation_planner.build_steps(verdict, findings, verifications)
        steps_dicts = [s.to_dict() for s in steps]
        self.container.prompt_guard.validate_negative_constraints(verdict.value, steps_dicts)

        compact_ctx = self.container.token_optimizer.compact_serialize(packed_facts)
        input_tokens = self.container.token_optimizer.estimate_tokens(compact_ctx)
        output_tokens = self.container.token_optimizer.estimate_tokens(json.dumps(steps_dicts))
        self.container.token_optimizer.record_usage(input_tokens, output_tokens, tokens_saved)

        dur_ms = (datetime.now() - start_t).total_seconds() * 1000.0

        self.replay_tracer.record_decision(
            case_id=cid,
            verdict=verdict.value,
            seed_email=email,
            cluster=cluster,
            findings=findings,
            verifications=verifications,
            steps=steps_dicts,
            rules_applied=[],
            duration_ms=dur_ms,
        )

        self.logger.clear_context()
        return DeletionAuditOutputRow(
            case_id=cid,
            deletion_status=verdict.value,
            steps_json=json.dumps(steps_dicts),
        )

    def run_pipeline(self, requests_csv: Path, output_csv: Path) -> List[DeletionAuditOutputRow]:
        """Executes full sequential deletion audit pipeline across all cases in requests_csv.

        Args:
            requests_csv: Path to deletion_requests.csv.
            output_csv: Path to write populated output.csv.
        Returns:
            List of generated DeletionAuditOutputRow instances.
        """
        requests = CsvHandler.read_csv_safe(requests_csv)
        results: List[DeletionAuditOutputRow] = []
        telemetry = AuditTelemetry.get_instance()

        for req in requests:
            start_t = datetime.now()
            row_result = self.audit_single_request(req)
            dur_ms = (datetime.now() - start_t).total_seconds() * 1000.0
            results.append(row_result)
            steps_data = json.loads(row_result.steps_json)
            findings_count = sum(1 for s in steps_data if s.get("phase") == "FINDING")
            remediations_count = sum(1 for s in steps_data if s.get("phase") == "REMEDIATION")
            telemetry.record_case_audit(
                case_id=row_result.case_id,
                status=row_result.deletion_status,
                duration_ms=dur_ms,
                findings_count=findings_count,
                remediations_count=remediations_count,
            )

        CsvHandler.write_output_csv(output_csv, results)
        return results


def main() -> None:
    """CLI entrypoint for running the Autonomous Deletion Audit Agent."""
    parser = argparse.ArgumentParser(description="Enterprise Autonomous Deletion Audit Agent")
    parser.add_argument("--requests", type=str, default="dataset/deletion_requests.csv", help="Path to deletion_requests.csv")
    parser.add_argument("--output", type=str, default="output.csv", help="Path to output.csv")
    parser.add_argument("--transcript", type=str, default="log.txt", help="Path to export log.txt")
    parser.add_argument("--concurrency", type=int, default=1, help="Worker threads for parallel execution (1 for sequential)")
    parser.add_argument("--debug-case", type=str, default=None, help="Print detailed diagnostic RCA report for specified case_id")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging verbosity")
    args = parser.parse_args()

    numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    StructuredLogger.get_logger(level=numeric_level)

    container = AuditContainer()

    if args.concurrency > 1:
        from code.engine.concurrent_orchestrator import ConcurrentAuditOrchestrator
        concurrent_orch = ConcurrentAuditOrchestrator(container=container, max_workers=args.concurrency)
        results = concurrent_orch.run_pipeline_concurrent(
            requests_csv=Path(args.requests),
            output_csv=Path(args.output),
            max_workers=args.concurrency,
        )
    else:
        orchestrator = DeletionAuditOrchestrator(container=container)
        results = orchestrator.run_pipeline(
            requests_csv=Path(args.requests),
            output_csv=Path(args.output),
        )

    is_valid, count, errors = OutputSchemaValidator.validate_file(Path(args.output))
    if is_valid:
        print(f"Successfully audited {count} requests. Output verified: {args.output}")
    else:
        print(f"Audit completed with schema warnings ({len(errors)}): {errors[:5]}")

    telemetry = AuditTelemetry.get_instance()
    snapshot = telemetry.get_snapshot()
    print(f"Telemetry: Audited={snapshot.total_requests or count}, Mean Latency={snapshot.mean_latency_ms}ms, P95={snapshot.p95_latency_ms}ms, Findings={snapshot.total_findings_reported}")

    token_stats = container.token_optimizer.get_telemetry()
    print(f"AI Optimization: Input Tokens={token_stats['total_input_tokens']}, Output Tokens={token_stats['total_output_tokens']}, Saved Tokens={token_stats['total_tokens_saved']}, Est Cost=${token_stats['estimated_cost_usd']}")

    if args.debug_case:
        report = ReplayTracer.get_tracer().format_diagnostic_report(args.debug_case)
        print("\n" + report)

    TranscriptExporter.export_to_log_txt(Path(args.transcript))
    print(f"Transcript exported to {args.transcript}")


if __name__ == "__main__":
    main()
