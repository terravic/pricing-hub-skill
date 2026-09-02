"""Real-Time Alert Dispatcher for Pricing Loads and SLA Breaches."""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.models.monitoring_models import (
    PricingHubAlert,
    AlertSeverity,
    PricingLoadRecord,
    LoadStatus,
)


class AlertDispatcher:
    """Dispatches and maintains real-time alerts for stalled loads, SLA risks, and validation failures."""

    def __init__(self):
        self.alerts: List[PricingHubAlert] = []

    def dispatch_stalled_load_alert(
        self,
        record: PricingLoadRecord,
        root_cause: str,
        action_required: str,
    ) -> PricingHubAlert:
        """Dispatches a CRITICAL alert when a pricing load stalls."""
        alert = PricingHubAlert(
            alert_id=f"ALT-STALL-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=AlertSeverity.CRITICAL,
            alert_type="STALLED_LOAD_DETECTED",
            message=f"Pricing Load '{record.load_id}' (Contract: {record.contract_id}) has STALLED. Reason: {root_cause}",
            load_id=record.load_id,
            action_required=action_required,
        )
        self.alerts.append(alert)
        return alert

    def dispatch_sla_breach_alert(
        self,
        record: PricingLoadRecord,
    ) -> PricingHubAlert:
        """Dispatches an alert when load duration exceeds its target SLA."""
        alert = PricingHubAlert(
            alert_id=f"ALT-SLA-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=AlertSeverity.WARNING if record.status != LoadStatus.STALLED else AlertSeverity.CRITICAL,
            alert_type="SLA_BREACH_WARNING",
            message=f"Pricing Load '{record.load_id}' has breached target SLA of {record.target_sla_seconds // 3600} hours (Elapsed: {record.elapsed_seconds // 3600} hours).",
            load_id=record.load_id,
            action_required="Escalate to Pricing Operations Lead; expedite bottleneck resolution.",
        )
        self.alerts.append(alert)
        return alert

    def dispatch_validation_failure_alert(
        self,
        load_id: str,
        failure_rate_pct: float,
        discrepancy_count: int,
    ) -> PricingHubAlert:
        """Dispatches an alert when batch allowable validation fails above tolerance."""
        alert = PricingHubAlert(
            alert_id=f"ALT-VAL-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=AlertSeverity.CRITICAL,
            alert_type="BATCH_VALIDATION_FAILURE",
            message=f"Quality gate breach in Load '{load_id}': {failure_rate_pct}% failure rate ({discrepancy_count} discrepancies).",
            load_id=load_id,
            action_required="Halt production migration. Inspect rate card differences and rerun parity checks.",
        )
        self.alerts.append(alert)
        return alert

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[PricingHubAlert]:
        if severity:
            return [a for a in self.alerts if a.severity == severity]
        return list(self.alerts)
