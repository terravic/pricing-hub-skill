"""Inpatient DRG Case Rate and Outlier Calculator."""

from typing import Dict, Any, Optional, Tuple
from src.models.claim_models import Claim, ClaimLine
from src.models.contract_models import ContractRateCard, PricingMethodology


class DRGFacilityCalculator:
    """Calculates inpatient facility allowable using CMS MS-DRG case rate methodologies and outliers."""

    def calculate_claim_drg(
        self,
        claim: Claim,
        line: ClaimLine,
        contract: ContractRateCard,
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """Calculates allowable for an inpatient DRG claim line."""
        drg_code = line.drg_code or claim.metadata.get("drg_code")
        if not drg_code or drg_code not in contract.drg_rules:
            return None, {"reason": f"DRG code '{drg_code}' not defined in contract rules."}

        rule = contract.drg_rules[drg_code]
        res = rule.calculate_allowable(claim.total_billed_amount)

        citation = contract.contract_clauses.get(
            "Section 4.2",
            f"Section 4.2 - Inpatient Facility DRG Adjudication (DRG {drg_code})"
        )

        audit = [
            f"Matched Inpatient DRG {drg_code}: {rule.description}",
            f"Base Rate: ${rule.base_rate:,.2f} x Weight: {rule.relative_weight} = ${res['base_payment']:,.2f}",
        ]
        if res["is_outlier"]:
            audit.append(
                f"Outlier Threshold Exceeded: Billed ${claim.total_billed_amount:,.2f} > ${rule.outlier_threshold:,.2f}. Marginal 80% add-on: ${res['outlier_payment']:,.2f}"
            )
        audit.append(f"Total DRG Allowable: ${res['total_allowable']:,.2f}")

        return res["total_allowable"], {
            "drg_code": drg_code,
            "base_payment": res["base_payment"],
            "outlier_payment": res["outlier_payment"],
            "is_outlier": res["is_outlier"],
            "allowable": res["total_allowable"],
            "contract_citations": [citation],
            "methodology": PricingMethodology.DRG_CASE_RATE,
            "audit_trail": audit,
        }
