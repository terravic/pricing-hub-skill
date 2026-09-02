"""Tests for Automated Allowable Verification and Discrepancy Detection."""

import pytest
from src.verification.discrepancy_detector import DiscrepancyDetector
from src.verification.audit_log_generator import AuditLogGenerator
from src.models.pricing_models import (
    PricedClaim,
    PricedClaimLine,
    ClaimLineDisposition,
    PricingMethodology,
    DiscrepancyType,
)
from src.models.claim_models import Claim, ClaimLine, ClaimType, LineOfBusiness


def test_discrepancy_detector_flags_allowable_mismatch():
    detector = DiscrepancyDetector(allowable_tolerance=0.01)

    priced = PricedClaim(
        claim_id="CLM-DISC-01",
        total_billed=250.0,
        total_allowable=165.00,
        overall_disposition=ClaimLineDisposition.PAID,
        contract_id="CTR-COMM-2026",
        lines=[
            PricedClaimLine(
                line_number=1,
                procedure_code="99214",
                billed_amount=250.0,
                allowable_amount=165.00,
                pricing_methodology=PricingMethodology.FEE_SCHEDULE,
                disposition=ClaimLineDisposition.PAID,
            )
        ],
    )

    # Expecting $180.00 (which differs from $165.00)
    ground_truth = {
        "claim_id": "CLM-DISC-01",
        "expected_total_allowable": 180.00,
        "expected_disposition": "PAID",
        "line_expectations": [
            {
                "line_number": 1,
                "expected_allowable": 180.00,
                "expected_disposition": "PAID",
            }
        ],
    }

    discrepancies = detector.compare_claim(priced, ground_truth)
    assert len(discrepancies) >= 1
    d = discrepancies[0]
    assert d.discrepancy_type == DiscrepancyType.ALLOWABLE_MISMATCH
    assert d.variance_amount == 15.00


def test_discrepancy_detector_flags_disposition_mismatch():
    detector = DiscrepancyDetector(allowable_tolerance=0.01)

    priced = PricedClaim(
        claim_id="CLM-DISC-02",
        total_billed=250.0,
        total_allowable=0.00,
        overall_disposition=ClaimLineDisposition.DENIED,
        contract_id="CTR-COMM-2026",
        lines=[
            PricedClaimLine(
                line_number=1,
                procedure_code="99214",
                billed_amount=250.0,
                allowable_amount=0.00,
                pricing_methodology=PricingMethodology.FEE_SCHEDULE,
                disposition=ClaimLineDisposition.DENIED,
            )
        ],
    )

    # Expected PAID
    ground_truth = {
        "claim_id": "CLM-DISC-02",
        "expected_total_allowable": 165.00,
        "expected_disposition": "PAID",
        "line_expectations": [
            {
                "line_number": 1,
                "expected_allowable": 165.00,
                "expected_disposition": "PAID",
            }
        ],
    }

    discrepancies = detector.compare_claim(priced, ground_truth)
    disp_discs = [d for d in discrepancies if d.discrepancy_type == DiscrepancyType.DISPOSITION_MISMATCH]
    assert len(disp_discs) >= 1


def test_audit_log_generation():
    claim = Claim(
        claim_id="CLM-AUDIT-01",
        claim_type=ClaimType.PROFESSIONAL,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="I10",
        lines=[ClaimLine(line_number=1, procedure_code="99214", billed_amount=250.0)],
        total_billed_amount=250.0,
    )

    priced = PricedClaim(
        claim_id="CLM-AUDIT-01",
        total_billed=250.0,
        total_allowable=165.00,
        overall_disposition=ClaimLineDisposition.PAID,
        contract_id="CTR-COMM-2026",
        lines=[
            PricedClaimLine(
                line_number=1,
                procedure_code="99214",
                billed_amount=250.0,
                allowable_amount=165.00,
                pricing_methodology=PricingMethodology.FEE_SCHEDULE,
                disposition=ClaimLineDisposition.PAID,
                contract_citations=["Section 3.1 - Standard Physician Fee Schedule"],
                audit_trail=["CPT 99214: Base rate $165.00 x 1.0 = $165.00"],
            )
        ],
    )

    gen = AuditLogGenerator()
    doc = gen.generate_claim_audit_trail(claim, priced)
    assert doc["claim_id"] == "CLM-AUDIT-01"
    assert doc["summary"]["overall_disposition"] == "PAID"
    assert len(doc["line_item_audit"]) == 1

    md = gen.format_markdown_report(doc)
    assert "### Claim Adjudication Audit Report: `CLM-AUDIT-01`" in md
    assert "Section 3.1" in md
