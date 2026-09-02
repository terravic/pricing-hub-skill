"""Automated Discrepancy Detection Engine."""

from typing import Dict, List, Any, Optional
from src.models.pricing_models import (
    PricedClaim,
    ClaimDiscrepancy,
    DiscrepancyType,
    ClaimLineDisposition,
)


class DiscrepancyDetector:
    """Compares calculated pricing results against expected ground-truth outcomes to detect variances."""

    def __init__(self, allowable_tolerance: float = 0.01):
        self.allowable_tolerance = allowable_tolerance

    def compare_claim(
        self,
        calculated: PricedClaim,
        ground_truth: Dict[str, Any],
    ) -> List[ClaimDiscrepancy]:
        """Compares a calculated PricedClaim against its ground-truth expectation."""
        discrepancies: List[ClaimDiscrepancy] = []

        expected_total = float(ground_truth.get("expected_total_allowable", 0.0))
        expected_disp = str(ground_truth.get("expected_disposition", "PAID")).upper()
        calc_disp = calculated.overall_disposition.value

        # 1. Total Allowable Check
        diff = round(abs(calculated.total_allowable - expected_total), 2)
        if diff > self.allowable_tolerance:
            pct = round((diff / expected_total * 100.0) if expected_total > 0 else 100.0, 4)
            discrepancies.append(ClaimDiscrepancy(
                claim_id=calculated.claim_id,
                line_number=0,  # 0 indicates claim-level
                discrepancy_type=DiscrepancyType.ALLOWABLE_MISMATCH,
                expected_allowable=expected_total,
                calculated_allowable=calculated.total_allowable,
                variance_amount=diff,
                variance_percentage=pct,
                expected_disposition=expected_disp,
                calculated_disposition=calc_disp,
                root_cause=f"Total allowable discrepancy: Expected ${expected_total:,.2f} vs Calculated ${calculated.total_allowable:,.2f} (Delta: ${diff:,.2f})",
            ))

        # 2. Overall Disposition Check
        if calc_disp != expected_disp:
            discrepancies.append(ClaimDiscrepancy(
                claim_id=calculated.claim_id,
                line_number=0,
                discrepancy_type=DiscrepancyType.DISPOSITION_MISMATCH,
                expected_allowable=expected_total,
                calculated_allowable=calculated.total_allowable,
                variance_amount=diff,
                variance_percentage=0.0,
                expected_disposition=expected_disp,
                calculated_disposition=calc_disp,
                root_cause=f"Overall disposition mismatch: Expected {expected_disp} but got {calc_disp}",
            ))

        # 3. Line-by-Line Checks
        line_expectations = {
            le["line_number"]: le for le in ground_truth.get("line_expectations", [])
        }

        for calc_line in calculated.lines:
            exp_line = line_expectations.get(calc_line.line_number)
            if not exp_line:
                continue

            exp_line_allowable = float(exp_line.get("expected_allowable", 0.0))
            exp_line_disp = str(exp_line.get("expected_disposition", "PAID")).upper()
            line_diff = round(abs(calc_line.allowable_amount - exp_line_allowable), 2)

            if line_diff > self.allowable_tolerance:
                pct = round((line_diff / exp_line_allowable * 100.0) if exp_line_allowable > 0 else 100.0, 4)
                discrepancies.append(ClaimDiscrepancy(
                    claim_id=calculated.claim_id,
                    line_number=calc_line.line_number,
                    discrepancy_type=DiscrepancyType.ALLOWABLE_MISMATCH,
                    expected_allowable=exp_line_allowable,
                    calculated_allowable=calc_line.allowable_amount,
                    variance_amount=line_diff,
                    variance_percentage=pct,
                    expected_disposition=exp_line_disp,
                    calculated_disposition=calc_line.disposition.value,
                    root_cause=f"Line {calc_line.line_number} allowable mismatch for CPT {calc_line.procedure_code}: Expected ${exp_line_allowable:,.2f} vs Calculated ${calc_line.allowable_amount:,.2f}",
                ))

            if calc_line.disposition.value != exp_line_disp:
                discrepancies.append(ClaimDiscrepancy(
                    claim_id=calculated.claim_id,
                    line_number=calc_line.line_number,
                    discrepancy_type=DiscrepancyType.DISPOSITION_MISMATCH,
                    expected_allowable=exp_line_allowable,
                    calculated_allowable=calc_line.allowable_amount,
                    variance_amount=line_diff,
                    variance_percentage=0.0,
                    expected_disposition=exp_line_disp,
                    calculated_disposition=calc_line.disposition.value,
                    root_cause=f"Line {calc_line.line_number} disposition mismatch: Expected {exp_line_disp} but got {calc_line.disposition.value}",
                ))

        return discrepancies
