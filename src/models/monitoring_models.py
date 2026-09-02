"""Domain models for Real-Time Pricing Load Monitoring, Stalled Bottleneck Tracking, and SLAs."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class LoadStatus(str, Enum):
    OUTSTANDING = "OUTSTANDING"  # Queued / In-flight
    LOADED = "LOADED"            # Successfully validated & ready for claim adjudication
    STALLED = "STALLED"          # Blocked by missing dependency, date overlap, or schema issue


class BottleneckReason(str, Enum):
    NONE = "NONE"
    MISSING_FEE_SCHEDULE = "MISSING_FEE_SCHEDULE"
    PROVIDER_NPI_UNMAPPED = "PROVIDER_NPI_UNMAPPED"
    RATE_CARD_DATE_OVERLAP = "RATE_CARD_DATE_OVERLAP"
    VALIDATION_VARIANCE_BREACH = "VALIDATION_VARIANCE_BREACH"
    SCHEMA_CORRUPTION = "SCHEMA_CORRUPTION"
    DEPENDENCY_TIMEOUT = "DEPENDENCY_TIMEOUT"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class PricingLoadRecord:
    load_id: str
    contract_id: str
    line_of_business: str
    total_claims: int
    loaded_claims: int = 0
    failed_claims: int = 0
    status: LoadStatus = LoadStatus.OUTSTANDING
    bottleneck_reason: BottleneckReason = BottleneckReason.NONE
    bottleneck_details: Optional[str] = None
    created_at: str = "2026-09-02T10:00:00Z"
    updated_at: str = "2026-09-02T10:00:00Z"
    target_sla_seconds: int = 14400  # 4 hours
    elapsed_seconds: int = 0
    estimated_completion_time: Optional[str] = None
    is_sla_breached: bool = False

    @property
    def completion_percentage(self) -> float:
        if self.total_claims == 0:
            return 100.0
        return round(((self.loaded_claims + self.failed_claims) / self.total_claims) * 100.0, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "load_id": self.load_id,
            "contract_id": self.contract_id,
            "line_of_business": self.line_of_business,
            "total_claims": self.total_claims,
            "loaded_claims": self.loaded_claims,
            "failed_claims": self.failed_claims,
            "status": self.status.value,
            "bottleneck_reason": self.bottleneck_reason.value,
            "bottleneck_details": self.bottleneck_details,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "target_sla_seconds": self.target_sla_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "completion_percentage": self.completion_percentage,
            "estimated_completion_time": self.estimated_completion_time,
            "is_sla_breached": self.is_sla_breached,
        }


@dataclass
class PricingHubAlert:
    alert_id: str
    timestamp: str
    severity: AlertSeverity
    alert_type: str
    message: str
    load_id: Optional[str] = None
    claim_id: Optional[str] = None
    action_required: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "alert_type": self.alert_type,
            "message": self.message,
            "load_id": self.load_id,
            "claim_id": self.claim_id,
            "action_required": self.action_required,
        }
