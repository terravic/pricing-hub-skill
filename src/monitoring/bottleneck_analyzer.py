"""Bottleneck Identification & Root-Cause Diagnostic Analyzer."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from src.models.monitoring_models import (
    BottleneckReason,
    PricingLoadRecord,
    LoadStatus,
)
from src.models.contract_models import ContractRateCard


class BottleneckAnalyzer:
    """Pinpoints bottlenecks in pricing loads and forecasts completion times."""

    def diagnose_load(
        self,
        record: PricingLoadRecord,
        contract: Optional[ContractRateCard] = None,
        provider_registered: bool = True,
        has_date_conflict: bool = False,
    ) -> Tuple[BottleneckReason, Optional[str], Optional[str]]:
        """Diagnoses why a load is STALLED or at risk of SLA breach.
        Returns (BottleneckReason, details, remediation_action).
        """
        # 1. Check Date Overlap
        if has_date_conflict:
            return (
                BottleneckReason.RATE_CARD_DATE_OVERLAP,
                f"Rate card effective dates [{contract.effective_start if contract else ''} - {contract.effective_end if contract else ''}] overlap with an existing active schedule for contract {record.contract_id}.",
                "Resolve date window boundaries in contract metadata before re-ingesting.",
            )

        # 2. Check Provider Credentialing / NPI Registration
        if not provider_registered:
            return (
                BottleneckReason.PROVIDER_NPI_UNMAPPED,
                f"Provider NPIs associated with contract '{record.contract_id}' are not mapped in provider credentialing registry.",
                "Map provider NPIs to active billing entity in Provider Master Index.",
            )

        # 3. Check Fee Schedule Completeness
        if contract and not contract.fee_schedule and not contract.drg_rules and not contract.percent_of_charges_rules:
            return (
                BottleneckReason.MISSING_FEE_SCHEDULE,
                f"Contract '{record.contract_id}' contains zero valid fee schedule entries, DRG rates, or percent of charge rules.",
                "Upload completed Exhibit A fee schedule file or DRG base rate schedule.",
            )

        # 4. Check Validation Variance Breach
        if record.total_claims > 0 and (record.failed_claims / record.total_claims) > 0.02:
            fail_pct = round((record.failed_claims / record.total_claims) * 100.0, 2)
            return (
                BottleneckReason.VALIDATION_VARIANCE_BREACH,
                f"Batch validation failure rate of {fail_pct}% exceeds the 2.0% quality gate threshold.",
                "Review discrepancy report, verify modifier rules (-25, -51), and update rate card parameters.",
            )

        # 5. Check Processing Dependency Timeout
        if record.status == LoadStatus.OUTSTANDING and record.elapsed_seconds > 7200:
            return (
                BottleneckReason.DEPENDENCY_TIMEOUT,
                f"Load processing time ({record.elapsed_seconds // 60} mins) exceeded outstanding threshold (120 mins).",
                "Restart pricing ingestion worker or inspect queue deadlocks.",
            )

        return BottleneckReason.NONE, None, None

    def calculate_eta(
        self,
        record: PricingLoadRecord,
        throughput_claims_per_sec: float = 250.0,
    ) -> Optional[str]:
        """Calculates Estimated Completion Time (ETA) for a load."""
        if record.status == LoadStatus.LOADED:
            return "COMPLETED"
        if record.status == LoadStatus.STALLED:
            return "STALLED - ETA PAUSED"

        remaining = max(0, record.total_claims - (record.loaded_claims + record.failed_claims))
        if throughput_claims_per_sec <= 0:
            return "UNKNOWN"

        secs_needed = remaining / throughput_claims_per_sec
        eta_dt = datetime.now(timezone.utc) + timedelta(seconds=secs_needed)
        return eta_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
