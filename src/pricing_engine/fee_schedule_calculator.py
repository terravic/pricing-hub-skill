"""Fee Schedule / RBRVS Rate Calculator."""

from typing import Dict, Any, Optional, Tuple, List
from src.models.claim_models import ClaimLine
from src.models.contract_models import ContractRateCard, PricingMethodology


class FeeScheduleCalculator:
    """Calculates allowable amounts based on contracted physician and outpatient fee schedules."""

    def calculate_line(
        self,
        line: ClaimLine,
        contract: ContractRateCard,
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """Calculates allowable for a single claim line against the contract fee schedule.
        Returns (allowable_amount, calculation_metadata).
        """
        proc_code = line.procedure_code
        modifiers = line.modifiers or []

        # Check for split modifiers 26 (Professional) or TC (Technical)
        target_key = proc_code
        split_applied = None
        if "26" in modifiers and f"{proc_code}-26" in contract.fee_schedule:
            target_key = f"{proc_code}-26"
            split_applied = "26 - Professional Component"
        elif "TC" in modifiers and f"{proc_code}-TC" in contract.fee_schedule:
            target_key = f"{proc_code}-TC"
            split_applied = "TC - Technical Component"

        if target_key in contract.fee_schedule:
            base_rate = contract.fee_schedule[target_key]
            allowable = round(base_rate * line.units, 2)

            citations = []
            if split_applied:
                citations.append(contract.contract_clauses.get("Section 6.4", "Section 6.4 - Diagnostic Splitting"))
            else:
                citations.append(contract.contract_clauses.get("Section 3.1", "Section 3.1 - Standard Physician Fee Schedule"))

            return allowable, {
                "matched_key": target_key,
                "base_rate": base_rate,
                "units": line.units,
                "allowable": allowable,
                "split_applied": split_applied,
                "contract_citations": citations,
                "methodology": PricingMethodology.FEE_SCHEDULE,
            }

        return None, {"reason": f"Procedure {proc_code} not found in fee schedule"}
