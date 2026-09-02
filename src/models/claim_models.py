"""Domain models for Claims (837P Professional & 837I Facility) and Scope Enforcement."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple


class LineOfBusiness(str, Enum):
    COMMERCIAL = "COMMERCIAL"
    MEDICARE = "MEDICARE"
    MEDICAID = "MEDICAID"


class ClaimType(str, Enum):
    PROFESSIONAL = "PROFESSIONAL"  # 837P / CMS-1500
    FACILITY = "FACILITY"          # 837I / UB-04
    DENTAL = "DENTAL"              # 837D / Excluded
    VISION = "VISION"              # Standalone retail/optometric / Excluded
    PHARMACY = "PHARMACY"          # NCPDP / NDC outpatient scripts / Excluded


class ClaimScopeStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass
class ClaimLine:
    line_number: int
    procedure_code: str  # CPT / HCPCS / CDT
    billed_amount: float
    units: float = 1.0
    revenue_code: Optional[str] = None  # Mandatory for Facility 837I
    modifiers: List[str] = field(default_factory=list)  # e.g., ["25"], ["26"], ["TC"], ["59"]
    service_date: str = "2026-01-15"
    place_of_service: Optional[str] = "11"  # Office, Hospital, etc.
    rendering_npi: Optional[str] = None
    drg_code: Optional[str] = None          # For Inpatient Facility
    is_carve_out: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_number": self.line_number,
            "procedure_code": self.procedure_code,
            "billed_amount": self.billed_amount,
            "units": self.units,
            "revenue_code": self.revenue_code,
            "modifiers": self.modifiers,
            "service_date": self.service_date,
            "place_of_service": self.place_of_service,
            "rendering_npi": self.rendering_npi,
            "drg_code": self.drg_code,
            "is_carve_out": self.is_carve_out,
        }


@dataclass
class Claim:
    claim_id: str
    claim_type: ClaimType
    line_of_business: LineOfBusiness
    member_id: str
    billing_provider_npi: str
    rendering_provider_npi: str
    principal_diagnosis: str
    lines: List[ClaimLine]
    total_billed_amount: float
    facility_type_code: Optional[str] = None  # e.g., "111" (Inpatient), "131" (Outpatient)
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    secondary_diagnoses: List[str] = field(default_factory=list)
    filing_date: str = "2026-02-01"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type.value,
            "line_of_business": self.line_of_business.value,
            "member_id": self.member_id,
            "billing_provider_npi": self.billing_provider_npi,
            "rendering_provider_npi": self.rendering_provider_npi,
            "principal_diagnosis": self.principal_diagnosis,
            "secondary_diagnoses": self.secondary_diagnoses,
            "facility_type_code": self.facility_type_code,
            "admission_date": self.admission_date,
            "discharge_date": self.discharge_date,
            "filing_date": self.filing_date,
            "total_billed_amount": self.total_billed_amount,
            "lines": [line.to_dict() for line in self.lines],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Claim":
        lines = [ClaimLine(**line) for line in data.get("lines", [])]
        claim_type = ClaimType(data.get("claim_type", "PROFESSIONAL"))
        lob = LineOfBusiness(data.get("line_of_business", "COMMERCIAL"))
        return cls(
            claim_id=data["claim_id"],
            claim_type=claim_type,
            line_of_business=lob,
            member_id=data["member_id"],
            billing_provider_npi=data["billing_provider_npi"],
            rendering_provider_npi=data["rendering_provider_npi"],
            principal_diagnosis=data["principal_diagnosis"],
            secondary_diagnoses=data.get("secondary_diagnoses", []),
            lines=lines,
            total_billed_amount=float(data["total_billed_amount"]),
            facility_type_code=data.get("facility_type_code"),
            admission_date=data.get("admission_date"),
            discharge_date=data.get("discharge_date"),
            filing_date=data.get("filing_date", "2026-02-01"),
            metadata=data.get("metadata", {}),
        )


def validate_claim_scope(claim: Claim) -> Tuple[bool, Optional[str]]:
    """Enforces scope boundaries:
    - Supported LOBs: Commercial, Medicare, Medicaid
    - Supported Claim Types: Professional, Facility
    - Excluded: Dental, Vision, Pharmacy
    """
    excluded_types = {ClaimType.DENTAL, ClaimType.VISION, ClaimType.PHARMACY}
    if claim.claim_type in excluded_types:
        return False, f"REJECT_UNSUPPORTED_LOB_EXCLUSION: Claim type '{claim.claim_type.value}' is excluded from Pricing Hub processing."

    valid_lobs = {LineOfBusiness.COMMERCIAL, LineOfBusiness.MEDICARE, LineOfBusiness.MEDICAID}
    if claim.line_of_business not in valid_lobs:
        return False, f"REJECT_UNSUPPORTED_LOB: Line of business '{claim.line_of_business.value}' is unsupported."

    return True, None
