"""Domain models for CMS LCD/NCD and Commercial Payer Reimbursement Policies."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any


class PolicyType(str, Enum):
    CMS_NCD = "CMS_NCD"
    CMS_LCD = "CMS_LCD"
    COMMERCIAL_REIMBURSEMENT = "COMMERCIAL_REIMBURSEMENT"
    MEDICAID_POLICY = "MEDICAID_POLICY"


class RuleAction(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REDUCE_50 = "REDUCE_50"
    SUSPEND_AUDIT = "SUSPEND_AUDIT"


@dataclass
class PolicyRule:
    policy_id: str
    policy_title: str
    policy_type: PolicyType
    paragraph_id: str
    target_procedure_codes: List[str]
    rule_action: RuleAction
    citation_text: str
    rule_description: str
    required_diagnosis_codes: List[str] = field(default_factory=list)
    bundled_exclusive_codes: List[str] = field(default_factory=list)
    required_modifiers: List[str] = field(default_factory=list)
    timely_filing_limit_days: Optional[int] = None
    denial_carc: Optional[str] = None  # e.g., "CO-16", "CO-97", "CO-29"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_title": self.policy_title,
            "policy_type": self.policy_type.value,
            "paragraph_id": self.paragraph_id,
            "target_procedure_codes": self.target_procedure_codes,
            "rule_action": self.rule_action.value,
            "citation_text": self.citation_text,
            "rule_description": self.rule_description,
            "required_diagnosis_codes": self.required_diagnosis_codes,
            "bundled_exclusive_codes": self.bundled_exclusive_codes,
            "required_modifiers": self.required_modifiers,
            "timely_filing_limit_days": self.timely_filing_limit_days,
            "denial_carc": self.denial_carc,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyRule":
        return cls(
            policy_id=data["policy_id"],
            policy_title=data["policy_title"],
            policy_type=PolicyType(data["policy_type"]),
            paragraph_id=data["paragraph_id"],
            target_procedure_codes=data.get("target_procedure_codes", []),
            rule_action=RuleAction(data["rule_action"]),
            citation_text=data["citation_text"],
            rule_description=data["rule_description"],
            required_diagnosis_codes=data.get("required_diagnosis_codes", []),
            bundled_exclusive_codes=data.get("bundled_exclusive_codes", []),
            required_modifiers=data.get("required_modifiers", []),
            timely_filing_limit_days=data.get("timely_filing_limit_days"),
            denial_carc=data.get("denial_carc"),
        )
