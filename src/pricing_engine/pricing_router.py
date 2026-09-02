"""Pricing Router & Claim Adjudication Engine."""

import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from src.models.claim_models import Claim, ClaimType
from src.models.contract_models import ContractRateCard, PricingMethodology
from src.models.policy_models import PolicyRule
from src.models.pricing_models import (
    PricedClaim,
    PricedClaimLine,
    ClaimLineDisposition,
)
from src.pricing_engine.fee_schedule_calculator import FeeScheduleCalculator
from src.pricing_engine.percent_charges_calculator import PercentChargesCalculator
from src.pricing_engine.drg_facility_calculator import DRGFacilityCalculator
from src.pricing_engine.mppr_modifier_evaluator import MPPRModifierEvaluator


class PricingRouter:
    """Central pricing router and methodology execution engine for the Pricing Hub."""

    def __init__(self):
        self.fee_calc = FeeScheduleCalculator()
        self.poc_calc = PercentChargesCalculator()
        self.drg_calc = DRGFacilityCalculator()
        self.mod_eval = MPPRModifierEvaluator()

    def price_claim(
        self,
        claim: Claim,
        contract: ContractRateCard,
        policies: Optional[List[PolicyRule]] = None,
    ) -> PricedClaim:
        """Adjudicates a claim against the contracted rate card and clinical policies."""
        start_time = time.time()
        policies = policies or []

        # 1. Global Claim Checks
        is_timely, timely_msg, timely_cit = self.mod_eval.check_timely_filing(claim, contract)
        is_high_dollar = self.mod_eval.check_high_dollar_threshold(claim)

        # 2. Multi-line relational evaluations
        mppr_map = self.mod_eval.evaluate_surgical_mppr(claim, contract)
        bundling_map = self.mod_eval.evaluate_bundling_edits(claim)

        priced_lines: List[PricedClaimLine] = []

        for line in claim.lines:
            # Case A: Timely filing violation
            if not is_timely:
                priced_lines.append(PricedClaimLine(
                    line_number=line.line_number,
                    procedure_code=line.procedure_code,
                    billed_amount=line.billed_amount,
                    allowable_amount=0.00,
                    pricing_methodology=PricingMethodology.FEE_SCHEDULE,
                    disposition=ClaimLineDisposition.DENIED,
                    units=line.units,
                    denial_reason_code="CO-29",
                    denial_reason_description=timely_msg,
                    policy_citations=[timely_cit] if timely_cit else [],
                    contract_citations=[contract.contract_clauses.get("Section 7.3", "Section 7.3 - Timely Filing Limit")],
                    audit_trail=[f"Line denied for timely filing breach: {timely_msg}"],
                ))
                continue

            # Case B: High-dollar inpatient threshold suspension
            if is_high_dollar:
                priced_lines.append(PricedClaimLine(
                    line_number=line.line_number,
                    procedure_code=line.procedure_code,
                    billed_amount=line.billed_amount,
                    allowable_amount=0.00,
                    pricing_methodology=PricingMethodology.DRG_CASE_RATE if line.drg_code else PricingMethodology.FEE_SCHEDULE,
                    disposition=ClaimLineDisposition.SUSPENDED,
                    units=line.units,
                    denial_reason_code=None,
                    denial_reason_description="Total billed amount exceeds $100,000 threshold. Suspended for manual clinician itemized review.",
                    policy_citations=["High Dollar Clinical Review Policy (> $100,000 threshold)"],
                    contract_citations=[contract.contract_clauses.get("Section 4.2", "Section 4.2 - Inpatient Case Rates")],
                    audit_trail=[f"Total billed ${claim.total_billed_amount:,.2f} exceeds $100k threshold. Claim line suspended for review."],
                ))
                continue

            # Case C: Bundled Service Edit (e.g. 99000)
            if line.line_number in bundling_map:
                b_info = bundling_map[line.line_number]
                priced_lines.append(PricedClaimLine(
                    line_number=line.line_number,
                    procedure_code=line.procedure_code,
                    billed_amount=line.billed_amount,
                    allowable_amount=0.00,
                    pricing_methodology=PricingMethodology.BUNDLED_PACKAGE,
                    disposition=ClaimLineDisposition.DENIED,
                    units=line.units,
                    denial_reason_code=b_info["carc_code"],
                    denial_reason_description=b_info["description"],
                    policy_citations=[b_info["policy_citation"]],
                    contract_citations=[contract.contract_clauses.get("Section 8.2", "Section 8.2 - Incidental Codes")],
                    audit_trail=[f"Bundled procedure {line.procedure_code} denied under {b_info['carc_code']}: {b_info['description']}"],
                ))
                continue

            # Case D: Medical Necessity Policy Verification (CMS LCD/NCD)
            med_nec_failure = self.mod_eval.evaluate_medical_necessity(claim, line, policies)
            if med_nec_failure:
                priced_lines.append(PricedClaimLine(
                    line_number=line.line_number,
                    procedure_code=line.procedure_code,
                    billed_amount=line.billed_amount,
                    allowable_amount=0.00,
                    pricing_methodology=PricingMethodology.FEE_SCHEDULE,
                    disposition=ClaimLineDisposition.DENIED,
                    units=line.units,
                    denial_reason_code=med_nec_failure["carc_code"],
                    denial_reason_description=med_nec_failure["description"],
                    policy_citations=[med_nec_failure["policy_citation"]],
                    contract_citations=[],
                    audit_trail=[f"Medical necessity failure for {line.procedure_code}: {med_nec_failure['description']}"],
                ))
                continue

            # Case E: Inpatient DRG Case Rate
            if line.drg_code and line.drg_code in contract.drg_rules:
                allowed, drg_details = self.drg_calc.calculate_claim_drg(claim, line, contract)
                priced_lines.append(PricedClaimLine(
                    line_number=line.line_number,
                    procedure_code=line.procedure_code,
                    billed_amount=line.billed_amount,
                    allowable_amount=allowed,
                    pricing_methodology=PricingMethodology.DRG_CASE_RATE,
                    disposition=ClaimLineDisposition.PAID,
                    units=line.units,
                    contract_citations=drg_details.get("contract_citations", []),
                    audit_trail=drg_details.get("audit_trail", []),
                ))
                continue

            # Case F: Percent of Charges (Revenue Code match e.g. 0270, 0360)
            if line.revenue_code:
                allowed, poc_details = self.poc_calc.calculate_line(line, contract)
                if allowed is not None:
                    priced_lines.append(PricedClaimLine(
                        line_number=line.line_number,
                        procedure_code=line.procedure_code,
                        billed_amount=line.billed_amount,
                        allowable_amount=allowed,
                        pricing_methodology=PricingMethodology.PERCENT_OF_CHARGES,
                        disposition=ClaimLineDisposition.PAID,
                        units=line.units,
                        contract_citations=poc_details.get("contract_citations", []),
                        audit_trail=[f"Revenue Code {line.revenue_code} matched category '{poc_details.get('category')}'. Applied {poc_details.get('percent_applied')*100}% allowable = ${allowed:,.2f}"],
                    ))
                    continue

            # Case G: MPPR Reduction
            if line.line_number in mppr_map and mppr_map[line.line_number].get("is_mppr"):
                m_info = mppr_map[line.line_number]
                allowed = m_info["allowable"]
                priced_lines.append(PricedClaimLine(
                    line_number=line.line_number,
                    procedure_code=line.procedure_code,
                    billed_amount=line.billed_amount,
                    allowable_amount=allowed,
                    pricing_methodology=PricingMethodology.MPPR_SURGICAL,
                    disposition=ClaimLineDisposition.PAID,
                    units=line.units,
                    policy_citations=[m_info["policy_citation"]],
                    contract_citations=[m_info["contract_citation"]],
                    audit_trail=[f"MPPR secondary surgical procedure: Rank {m_info['rank']} discounted by 50% = ${allowed:,.2f}"],
                ))
                continue

            # Case H: Standard Fee Schedule
            allowed, fs_details = self.fee_calc.calculate_line(line, contract)
            if allowed is not None:
                audit = [f"CPT/HCPCS {line.procedure_code}: Base rate ${fs_details['base_rate']:,.2f} x {line.units} units = ${allowed:,.2f}"]
                if fs_details.get("split_applied"):
                    audit.append(f"Diagnostic split applied: {fs_details['split_applied']}")

                policy_cits = []
                if "25" in line.modifiers:
                    policy_cits.append("PAYER-RP-109, Paragraph 3.2")

                priced_lines.append(PricedClaimLine(
                    line_number=line.line_number,
                    procedure_code=line.procedure_code,
                    billed_amount=line.billed_amount,
                    allowable_amount=allowed,
                    pricing_methodology=PricingMethodology.FEE_SCHEDULE,
                    disposition=ClaimLineDisposition.PAID,
                    units=line.units,
                    policy_citations=policy_cits,
                    contract_citations=fs_details.get("contract_citations", []),
                    audit_trail=audit,
                ))
            else:
                # Unpriced line fallback
                priced_lines.append(PricedClaimLine(
                    line_number=line.line_number,
                    procedure_code=line.procedure_code,
                    billed_amount=line.billed_amount,
                    allowable_amount=0.00,
                    pricing_methodology=PricingMethodology.FEE_SCHEDULE,
                    disposition=ClaimLineDisposition.DENIED,
                    units=line.units,
                    denial_reason_code="CO-16",
                    denial_reason_description=fs_details.get("reason", "Procedure not contracted."),
                    audit_trail=["Procedure code not found on contract rate card."],
                ))

        # Determine overall claim disposition
        if is_high_dollar:
            overall_disp = ClaimLineDisposition.SUSPENDED
        elif all(pl.disposition == ClaimLineDisposition.DENIED for pl in priced_lines):
            overall_disp = ClaimLineDisposition.DENIED
        else:
            overall_disp = ClaimLineDisposition.PAID

        total_allowed = round(sum(pl.allowable_amount for pl in priced_lines), 2)
        exec_ms = round((time.time() - start_time) * 1000.0, 2)

        return PricedClaim(
            claim_id=claim.claim_id,
            total_billed=claim.total_billed_amount,
            total_allowable=total_allowed,
            overall_disposition=overall_disp,
            contract_id=contract.contract_id,
            lines=priced_lines,
            adjudication_timestamp=datetime.now(timezone.utc).isoformat(),
            execution_time_ms=exec_ms,
        )
