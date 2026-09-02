"""Real-Time Pricing Load Tracker & Bottleneck Monitoring System."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from src.models.monitoring_models import (
    PricingLoadRecord,
    LoadStatus,
    BottleneckReason,
    PricingHubAlert,
    AlertSeverity,
)
from src.monitoring.bottleneck_analyzer import BottleneckAnalyzer
from src.monitoring.alert_dispatcher import AlertDispatcher
from src.models.contract_models import ContractRateCard


class PricingLoadTracker:
    """Monitors all pricing loads in real time, categorizes statuses, and pinpoints bottlenecks."""

    def __init__(self, target_sla_seconds: int = 14400):
        self.target_sla_seconds = target_sla_seconds
        self.loads: Dict[str, PricingLoadRecord] = {}
        self.analyzer = BottleneckAnalyzer()
        self.dispatcher = AlertDispatcher()

    def register_load(
        self,
        contract_id: str,
        line_of_business: str,
        total_claims: int,
        load_id: Optional[str] = None,
    ) -> PricingLoadRecord:
        """Registers a new pricing load in the pipeline with OUTSTANDING status."""
        lid = load_id or f"LOAD-{line_of_business[:4]}-{uuid.uuid4().hex[:6].upper()}"
        now_str = datetime.now(timezone.utc).isoformat()

        record = PricingLoadRecord(
            load_id=lid,
            contract_id=contract_id,
            line_of_business=line_of_business,
            total_claims=total_claims,
            loaded_claims=0,
            failed_claims=0,
            status=LoadStatus.OUTSTANDING,
            bottleneck_reason=BottleneckReason.NONE,
            created_at=now_str,
            updated_at=now_str,
            target_sla_seconds=self.target_sla_seconds,
            elapsed_seconds=0,
            is_sla_breached=False,
        )
        record.estimated_completion_time = self.analyzer.calculate_eta(record)
        self.loads[lid] = record
        return record

    def update_progress(
        self,
        load_id: str,
        loaded_increment: int = 0,
        failed_increment: int = 0,
        elapsed_seconds: Optional[int] = None,
        contract: Optional[ContractRateCard] = None,
        provider_registered: bool = True,
        has_date_conflict: bool = False,
    ) -> PricingLoadRecord:
        """Updates claim processing counts and checks for bottlenecks/SLAs."""
        record = self.loads.get(load_id)
        if not record:
            raise ValueError(f"Pricing load '{load_id}' not found.")

        record.loaded_claims += loaded_increment
        record.failed_claims += failed_increment
        if elapsed_seconds is not None:
            record.elapsed_seconds = elapsed_seconds

        record.updated_at = datetime.now(timezone.utc).isoformat()

        # Check SLA breach
        if record.elapsed_seconds > record.target_sla_seconds and not record.is_sla_breached:
            record.is_sla_breached = True
            self.dispatcher.dispatch_sla_breach_alert(record)

        # Run Bottleneck Diagnostic
        reason, details, action = self.analyzer.diagnose_load(
            record,
            contract=contract,
            provider_registered=provider_registered,
            has_date_conflict=has_date_conflict,
        )

        if reason != BottleneckReason.NONE:
            record.status = LoadStatus.STALLED
            record.bottleneck_reason = reason
            record.bottleneck_details = details
            self.dispatcher.dispatch_stalled_load_alert(record, details, action)
        elif (record.loaded_claims + record.failed_claims) >= record.total_claims and record.total_claims > 0:
            record.status = LoadStatus.LOADED
            record.bottleneck_reason = BottleneckReason.NONE
            record.bottleneck_details = None

        record.estimated_completion_time = self.analyzer.calculate_eta(record)
        return record

    def mark_stalled(
        self,
        load_id: str,
        reason: BottleneckReason,
        details: str,
        action_required: str,
    ) -> PricingLoadRecord:
        """Manually forces a load to STALLED status with root cause."""
        record = self.loads.get(load_id)
        if not record:
            raise ValueError(f"Pricing load '{load_id}' not found.")

        record.status = LoadStatus.STALLED
        record.bottleneck_reason = reason
        record.bottleneck_details = details
        record.updated_at = datetime.now(timezone.utc).isoformat()
        record.estimated_completion_time = "STALLED"
        self.dispatcher.dispatch_stalled_load_alert(record, details, action_required)
        return record

    def mark_completed(self, load_id: str) -> PricingLoadRecord:
        """Marks a load as LOADED (ready for claim execution)."""
        record = self.loads.get(load_id)
        if not record:
            raise ValueError(f"Pricing load '{load_id}' not found.")

        record.status = LoadStatus.LOADED
        record.loaded_claims = record.total_claims - record.failed_claims
        record.bottleneck_reason = BottleneckReason.NONE
        record.bottleneck_details = None
        record.updated_at = datetime.now(timezone.utc).isoformat()
        record.estimated_completion_time = "COMPLETED"
        return record

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Returns real-time pipeline status breakdown and bottleneck overview."""
        all_records = list(self.loads.values())
        loaded = sum(1 for r in all_records if r.status == LoadStatus.LOADED)
        outstanding = sum(1 for r in all_records if r.status == LoadStatus.OUTSTANDING)
        stalled = sum(1 for r in all_records if r.status == LoadStatus.STALLED)
        sla_breached = sum(1 for r in all_records if r.is_sla_breached)

        stalled_details = [
            {
                "load_id": r.load_id,
                "contract_id": r.contract_id,
                "reason": r.bottleneck_reason.value,
                "details": r.bottleneck_details,
                "elapsed_hours": round(r.elapsed_seconds / 3600, 1),
            }
            for r in all_records if r.status == LoadStatus.STALLED
        ]

        return {
            "total_loads": len(all_records),
            "status_counts": {
                "LOADED": loaded,
                "OUTSTANDING": outstanding,
                "STALLED": stalled,
            },
            "sla_breaches": sla_breached,
            "stalled_bottlenecks": stalled_details,
            "active_alerts_count": len(self.dispatcher.alerts),
        }
