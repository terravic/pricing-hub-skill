"""Domain models for Provider Contracts, Rate Cards, and Pricing Methodologies."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from src.models.claim_models import LineOfBusiness


class PricingMethodology(str, Enum):
    FEE_SCHEDULE = "FEE_SCHEDULE"
    PERCENT_OF_CHARGES = "PERCENT_OF_CHARGES"
    PER_DIEM = "PER_DIEM"
    DRG_CASE_RATE = "DRG_CASE_RATE"
    MPPR_SURGICAL = "MPPR_SURGICAL"
    BUNDLED_PACKAGE = "BUNDLED_PACKAGE"


@dataclass
class DRGRule:
    drg_code: str
    description: str
    base_rate: float
    relative_weight: float
    outlier_threshold: float = 45000.0
    outlier_marginal_rate: float = 0.80  # 80% marginal payment above threshold

    def calculate_allowable(self, total_billed: float) -> Dict[str, Any]:
        base_payment = round(self.base_rate * self.relative_weight, 2)
        outlier_payment = 0.0
        is_outlier = False
        if total_billed > self.outlier_threshold:
            is_outlier = True
            outlier_payment = round((total_billed - self.outlier_threshold) * self.outlier_marginal_rate, 2)
        total_allowable = round(base_payment + outlier_payment, 2)
        return {
            "base_payment": base_payment,
            "outlier_payment": outlier_payment,
            "is_outlier": is_outlier,
            "total_allowable": total_allowable,
        }


@dataclass
class PercentOfChargesRule:
    category: str
    revenue_code_prefix: Optional[str]
    percent_allowable: float  # e.g., 0.65 for 65% of billed charges


@dataclass
class MPPRRule:
    primary_percentage: float = 1.00   # 100% of fee schedule
    secondary_percentage: float = 0.50 # 50% of fee schedule
    tertiary_percentage: float = 0.50  # 50% of fee schedule


@dataclass
class ContractRateCard:
    contract_id: str
    contract_name: str
    line_of_business: LineOfBusiness
    provider_npi_list: List[str]
    effective_start: str
    effective_end: str
    fee_schedule: Dict[str, float] = field(default_factory=dict)
    drg_rules: Dict[str, DRGRule] = field(default_factory=dict)
    percent_of_charges_rules: List[PercentOfChargesRule] = field(default_factory=list)
    per_diem_rates: Dict[str, float] = field(default_factory=dict)  # rev_code -> daily rate
    mppr_rule: MPPRRule = field(default_factory=MPPRRule)
    contract_clauses: Dict[str, str] = field(default_factory=dict)  # section_id -> text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_name": self.contract_name,
            "line_of_business": self.line_of_business.value,
            "provider_npi_list": self.provider_npi_list,
            "effective_start": self.effective_start,
            "effective_end": self.effective_end,
            "fee_schedule": self.fee_schedule,
            "drg_rules": {
                k: {
                    "drg_code": v.drg_code,
                    "description": v.description,
                    "base_rate": v.base_rate,
                    "relative_weight": v.relative_weight,
                    "outlier_threshold": v.outlier_threshold,
                    "outlier_marginal_rate": v.outlier_marginal_rate,
                }
                for k, v in self.drg_rules.items()
            },
            "percent_of_charges_rules": [
                {
                    "category": r.category,
                    "revenue_code_prefix": r.revenue_code_prefix,
                    "percent_allowable": r.percent_allowable,
                }
                for r in self.percent_of_charges_rules
            ],
            "per_diem_rates": self.per_diem_rates,
            "contract_clauses": self.contract_clauses,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContractRateCard":
        drg_rules = {}
        for k, v in data.get("drg_rules", {}).items():
            drg_rules[k] = DRGRule(**v)

        poc_rules = []
        for r in data.get("percent_of_charges_rules", []):
            poc_rules.append(PercentOfChargesRule(**r))

        return cls(
            contract_id=data["contract_id"],
            contract_name=data["contract_name"],
            line_of_business=LineOfBusiness(data["line_of_business"]),
            provider_npi_list=data.get("provider_npi_list", []),
            effective_start=data["effective_start"],
            effective_end=data["effective_end"],
            fee_schedule=data.get("fee_schedule", {}),
            drg_rules=drg_rules,
            percent_of_charges_rules=poc_rules,
            per_diem_rates=data.get("per_diem_rates", {}),
            contract_clauses=data.get("contract_clauses", {}),
        )
