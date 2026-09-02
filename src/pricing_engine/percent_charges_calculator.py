"""Percent of Billed Charges Rate Calculator."""

from typing import Dict, Any, Optional, Tuple, List
from src.models.claim_models import ClaimLine
from src.models.contract_models import ContractRateCard, PricingMethodology


class PercentChargesCalculator:
    """Calculates allowable based on contractual percentage of billed charges."""

    def calculate_line(
        self,
        line: ClaimLine,
        contract: ContractRateCard,
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """Calculates allowable for lines billed under revenue code or unlisted charges."""
        rev_code = line.revenue_code or ""

        for rule in contract.percent_of_charges_rules:
            prefix = rule.revenue_code_prefix
            if prefix and rev_code.startswith(prefix):
                allowable = round(line.billed_amount * rule.percent_allowable, 2)
                citation = contract.contract_clauses.get("Section 3.2", "Section 3.2 - Percent of Billed Charges")
                return allowable, {
                    "category": rule.category,
                    "percent_applied": rule.percent_allowable,
                    "billed_amount": line.billed_amount,
                    "allowable": allowable,
                    "contract_citations": [citation],
                    "methodology": PricingMethodology.PERCENT_OF_CHARGES,
                }

        return None, {"reason": "No matching percent of charges rule for line"}
