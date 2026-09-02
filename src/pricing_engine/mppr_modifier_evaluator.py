"""Evaluator for Modifiers (-25, -26, -TC, -51), MPPR, Bundling, Timely Filing, and Medical Necessity."""

from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from src.models.claim_models import Claim, ClaimLine
from src.models.contract_models import ContractRateCard, PricingMethodology
from src.models.policy_models import PolicyRule
from src.models.pricing_models import ClaimLineDisposition


class MPPRModifierEvaluator:
    """Evaluates clinical and procedural modifiers, multi-procedure reductions, and policy edits."""

    def __init__(self):
        pass

    def check_timely_filing(self, claim: Claim, contract: ContractRateCard) -> Tuple[bool, Optional[str], Optional[str]]:
        """Checks if the claim filing date violates timely filing limits."""
        # Commercial standard: 90 days; Medicare: 365 days; Medicaid: 180 days
        limit_days = 90 if claim.line_of_business.value == "COMMERCIAL" else 365 if claim.line_of_business.value == "MEDICARE" else 180

        try:
            earliest_service = min(l.service_date for l in claim.lines)
            dt_service = datetime.strptime(earliest_service, "%Y-%m-%d")
            dt_filing = datetime.strptime(claim.filing_date, "%Y-%m-%d")
            diff_days = (dt_filing - dt_service).days

            if diff_days > limit_days:
                return (
                    False,
                    f"Claim filed {diff_days} days after service (limit: {limit_days} days).",
                    "PAYER-RP-003, Paragraph 1.2",
                )
        except Exception:
            pass

        return True, None, None

    def check_high_dollar_threshold(self, claim: Claim) -> bool:
        """Flags high-dollar facility encounters exceeding $100,000 for manual clinician review."""
        return claim.total_billed_amount >= 100000.0

    def evaluate_surgical_mppr(
        self,
        claim: Claim,
        contract: ContractRateCard,
    ) -> Dict[int, Dict[str, Any]]:
        """Identifies multiple surgical procedures and calculates MPPR rankings and rates."""
        surgical_lines: List[Tuple[ClaimLine, float]] = []

        for line in claim.lines:
            # Check if procedure is surgical (e.g. 29881, 29882)
            if line.procedure_code in ["29881", "29882", "45378", "45380"]:
                base_fs = contract.fee_schedule.get(line.procedure_code, 0.0)
                if base_fs > 0:
                    surgical_lines.append((line, base_fs))

        if len(surgical_lines) <= 1:
            return {}

        mppr_results: Dict[int, Dict[str, Any]] = {}
        # Check if specific lines have modifier 51 explicitly designating secondary reduction
        lines_with_mod51 = [s_line.line_number for s_line, _ in surgical_lines if "51" in s_line.modifiers]

        if lines_with_mod51:
            for s_line, base_rate in surgical_lines:
                if s_line.line_number in lines_with_mod51:
                    mppr_results[s_line.line_number] = {
                        "is_mppr": True,
                        "rank": 2,
                        "percentage": 0.50,
                        "allowable": round(base_rate * 0.50, 2),
                        "methodology": PricingMethodology.MPPR_SURGICAL,
                        "policy_citation": "PAYER-RP-042, Paragraph 4.1",
                        "contract_citation": contract.contract_clauses.get("Section 5.1", "Section 5.1 - Multiple Procedure Reductions"),
                    }
                else:
                    mppr_results[s_line.line_number] = {
                        "is_mppr": False,
                        "rank": 1,
                        "percentage": 1.0,
                        "allowable": base_rate,
                        "methodology": PricingMethodology.FEE_SCHEDULE,
                    }
            return mppr_results

        # Fallback: Sort surgical lines descending by base fee schedule rate
        # Primary procedure gets 100%, secondary gets 50%
        surgical_lines.sort(key=lambda x: x[1], reverse=True)

        for rank, (s_line, base_rate) in enumerate(surgical_lines):
            if rank == 0:
                mppr_results[s_line.line_number] = {
                    "is_mppr": False,
                    "rank": 1,
                    "percentage": 1.0,
                    "allowable": base_rate,
                    "methodology": PricingMethodology.FEE_SCHEDULE,
                }
            else:
                mppr_results[s_line.line_number] = {
                    "is_mppr": True,
                    "rank": rank + 1,
                    "percentage": 0.50,
                    "allowable": round(base_rate * 0.50, 2),
                    "methodology": PricingMethodology.MPPR_SURGICAL,
                    "policy_citation": "PAYER-RP-042, Paragraph 4.1",
                    "contract_citation": contract.contract_clauses.get("Section 5.1", "Section 5.1 - Multiple Procedure Reductions"),
                }

        return mppr_results

    def evaluate_bundling_edits(self, claim: Claim) -> Dict[int, Dict[str, Any]]:
        """Checks for incidental or bundled codes (e.g., CPT 99000 billed with office visit or lab)."""
        proc_codes = {l.procedure_code for l in claim.lines}
        bundling_results = {}

        for line in claim.lines:
            if line.procedure_code == "99000":
                if any(code in proc_codes for code in ["36415", "99213", "99214", "99215"]):
                    bundling_results[line.line_number] = {
                        "bundled": True,
                        "allowable": 0.00,
                        "disposition": ClaimLineDisposition.DENIED,
                        "carc_code": "CO-97",
                        "description": "Bundled service; payment included in primary procedure.",
                        "policy_citation": "PAYER-RP-018, Paragraph 5.1",
                    }

        return bundling_results

    def evaluate_medical_necessity(self, claim: Claim, line: ClaimLine, policies: List[PolicyRule]) -> Optional[Dict[str, Any]]:
        """Verifies clinical indications against CMS LCD/NCD policies."""
        for pol in policies:
            if line.procedure_code in pol.target_procedure_codes:
                if pol.required_diagnosis_codes:
                    all_claim_diags = [claim.principal_diagnosis] + claim.secondary_diagnoses
                    matched = any(diag in pol.required_diagnosis_codes for diag in all_claim_diags)
                    if not matched:
                        return {
                            "passed": False,
                            "allowable": 0.00,
                            "disposition": ClaimLineDisposition.DENIED,
                            "carc_code": pol.denial_carc or "CO-16",
                            "description": f"Diagnosis does not meet medical necessity under {pol.policy_id}.",
                            "policy_citation": f"{pol.policy_id}, {pol.paragraph_id}",
                        }
        return None
