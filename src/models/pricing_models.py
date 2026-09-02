"""Domain models for Adjudicated Claims, Discrepancies, and Audit Trail."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from src.models.contract_models import PricingMethodology


class ClaimLineDisposition(str, Enum):
    PAID = "PAID"
    DENIED = "DENIED"
    SUSPENDED = "SUSPENDED"


class DiscrepancyType(str, Enum):
    ALLOWABLE_MISMATCH = "ALLOWABLE_MISMATCH"
    UNEXPECTED_DENIAL = "UNEXPECTED_DENIAL"
    UNEXPECTED_APPROVAL = "UNEXPECTED_APPROVAL"
    DISPOSITION_MISMATCH = "DISPOSITION_MISMATCH"
    MODIFIER_RULE_MISMATCH = "MODIFIER_RULE_MISMATCH"
    SCOPE_REJECTION = "SCOPE_REJECTION"


@dataclass
class PricedClaimLine:
    line_number: int
    procedure_code: str
    billed_amount: float
    allowable_amount: float
    pricing_methodology: PricingMethodology
    disposition: ClaimLineDisposition
    units: float = 1.0
    denial_reason_code: Optional[str] = None         # e.g., "CO-16", "CO-97", "CO-45", "CO-29"
    denial_reason_description: Optional[str] = None
    policy_citations: List[str] = field(default_factory=list)
    contract_citations: List[str] = field(default_factory=list)
    audit_trail: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_number": self.line_number,
            "procedure_code": self.procedure_code,
            "billed_amount": self.billed_amount,
            "allowable_amount": self.allowable_amount,
            "units": self.units,
            "pricing_methodology": self.pricing_methodology.value,
            "disposition": self.disposition.value,
            "denial_reason_code": self.denial_reason_code,
            "denial_reason_description": self.denial_reason_description,
            "policy_citations": self.policy_citations,
            "contract_citations": self.contract_citations,
            "audit_trail": self.audit_trail,
        }


@dataclass
class PricedClaim:
    claim_id: str
    total_billed: float
    total_allowable: float
    overall_disposition: ClaimLineDisposition
    contract_id: str
    lines: List[PricedClaimLine]
    adjudication_timestamp: str = "2026-09-02T12:00:00Z"
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "total_billed": self.total_billed,
            "total_allowable": self.total_allowable,
            "overall_disposition": self.overall_disposition.value,
            "contract_id": self.contract_id,
            "adjudication_timestamp": self.adjudication_timestamp,
            "execution_time_ms": self.execution_time_ms,
            "lines": [line.to_dict() for line in self.lines],
        }


@dataclass
class ClaimDiscrepancy:
    claim_id: str
    line_number: int
    discrepancy_type: DiscrepancyType
    expected_allowable: float
    calculated_allowable: float
    variance_amount: float
    variance_percentage: float
    expected_disposition: str
    calculated_disposition: str
    root_cause: str
    audit_citation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "line_number": self.line_number,
            "discrepancy_type": getattr(self.discrepancy_type, "value", str(self.discrepancy_type)),
            "expected_allowable": self.expected_allowable,
            "calculated_allowable": self.calculated_allowable,
            "variance_amount": round(self.variance_amount, 2),
            "variance_percentage": round(self.variance_percentage, 4),
            "expected_disposition": self.expected_disposition,
            "calculated_disposition": self.calculated_disposition,
            "root_cause": self.root_cause,
            "audit_citation": self.audit_citation,
        }
