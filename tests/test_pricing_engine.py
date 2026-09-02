"""Tests for Pricing Engine Calculators, Modifiers, and Router."""

import pytest
from src.ingestion.contract_parser import ContractParser
from src.ingestion.policy_parser import PolicyParser
from src.pricing_engine.pricing_router import PricingRouter
from src.models.claim_models import Claim, ClaimLine, ClaimType, LineOfBusiness
from src.models.pricing_models import ClaimLineDisposition, PricingMethodology


@pytest.fixture
def test_setup():
    cp = ContractParser()
    cp.load_directory("data/contracts")
    contract = cp.get_contract_by_id("CTR-COMM-2026")

    pp = PolicyParser()
    pp.load_directory("data/policies")
    policies = list(pp.policies.values())

    router = PricingRouter()
    return {"contract": contract, "policies": policies, "router": router}


def test_standard_fee_schedule_pricing(test_setup):
    router = test_setup["router"]
    contract = test_setup["contract"]
    policies = test_setup["policies"]

    claim = Claim(
        claim_id="TEST-FS-01",
        claim_type=ClaimType.PROFESSIONAL,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="I10",
        lines=[ClaimLine(line_number=1, procedure_code="99214", billed_amount=250.0)],
        total_billed_amount=250.0,
    )
    priced = router.price_claim(claim, contract, policies)
    assert priced.total_allowable == 165.00
    assert priced.overall_disposition == ClaimLineDisposition.PAID
    assert priced.lines[0].pricing_methodology == PricingMethodology.FEE_SCHEDULE


def test_diagnostic_split_modifiers_26_and_tc(test_setup):
    router = test_setup["router"]
    contract = test_setup["contract"]
    policies = test_setup["policies"]

    # Professional Component (-26)
    claim_26 = Claim(
        claim_id="TEST-SPLIT-26",
        claim_type=ClaimType.PROFESSIONAL,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="R05.9",
        lines=[ClaimLine(line_number=1, procedure_code="71046", billed_amount=150.0, modifiers=["26"])],
        total_billed_amount=150.0,
    )
    priced_26 = router.price_claim(claim_26, contract, policies)
    assert priced_26.total_allowable == 35.00  # 71046-26 rate

    # Technical Component (-TC)
    claim_tc = Claim(
        claim_id="TEST-SPLIT-TC",
        claim_type=ClaimType.PROFESSIONAL,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="R05.9",
        lines=[ClaimLine(line_number=1, procedure_code="71046", billed_amount=150.0, modifiers=["TC"])],
        total_billed_amount=150.0,
    )
    priced_tc = router.price_claim(claim_tc, contract, policies)
    assert priced_tc.total_allowable == 50.00  # 71046-TC rate


def test_mppr_surgical_reduction(test_setup):
    router = test_setup["router"]
    contract = test_setup["contract"]
    policies = test_setup["policies"]

    claim = Claim(
        claim_id="TEST-MPPR-01",
        claim_type=ClaimType.PROFESSIONAL,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="M23.22",
        lines=[
            ClaimLine(line_number=1, procedure_code="99214", billed_amount=300.0, modifiers=["25"]),
            ClaimLine(line_number=2, procedure_code="29881", billed_amount=3000.0),
            ClaimLine(line_number=3, procedure_code="29882", billed_amount=2800.0, modifiers=["51"]),
        ],
        total_billed_amount=6100.0,
    )
    priced = router.price_claim(claim, contract, policies)
    # Line 1: 165.00
    # Line 2 (29881): 1250.00
    # Line 3 (29882 reduced 50%): 700.00
    assert priced.total_allowable == 2115.00
    assert priced.lines[2].allowable_amount == 700.00
    assert priced.lines[2].pricing_methodology == PricingMethodology.MPPR_SURGICAL
    assert "PAYER-RP-042, Paragraph 4.1" in priced.lines[2].policy_citations


def test_inpatient_drg_and_outlier(test_setup):
    router = test_setup["router"]
    contract = test_setup["contract"]
    policies = test_setup["policies"]

    # Base DRG 470 (without outlier): 10,500 * 1.95 = 20,475.00
    claim_base = Claim(
        claim_id="TEST-DRG-BASE",
        claim_type=ClaimType.FACILITY,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1548291034",
        rendering_provider_npi="1548291034",
        principal_diagnosis="M16.11",
        facility_type_code="111",
        lines=[ClaimLine(line_number=1, procedure_code="0001", revenue_code="0110", billed_amount=30000.0, drg_code="470")],
        total_billed_amount=30000.0,
    )
    priced_base = router.price_claim(claim_base, contract, policies)
    assert priced_base.total_allowable == 20475.00

    # High-Cost Outlier (Billed $55,000 > $45,000 threshold)
    # Base: 20475 + (55000 - 45000) * 0.80 = 8000 -> 28475.00
    claim_outlier = Claim(
        claim_id="TEST-DRG-OUTLIER",
        claim_type=ClaimType.FACILITY,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1548291034",
        rendering_provider_npi="1548291034",
        principal_diagnosis="M16.11",
        facility_type_code="111",
        lines=[ClaimLine(line_number=1, procedure_code="0001", revenue_code="0110", billed_amount=55000.0, drg_code="470")],
        total_billed_amount=55000.0,
    )
    priced_outlier = router.price_claim(claim_outlier, contract, policies)
    assert priced_outlier.total_allowable == 28475.00


def test_bundling_edit_denial(test_setup):
    router = test_setup["router"]
    contract = test_setup["contract"]
    policies = test_setup["policies"]

    claim = Claim(
        claim_id="TEST-BUNDLE",
        claim_type=ClaimType.PROFESSIONAL,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="E11.9",
        lines=[
            ClaimLine(line_number=1, procedure_code="36415", billed_amount=25.0),
            ClaimLine(line_number=2, procedure_code="99000", billed_amount=30.0),
        ],
        total_billed_amount=55.0,
    )
    priced = router.price_claim(claim, contract, policies)
    assert priced.lines[0].allowable_amount == 15.00
    assert priced.lines[1].allowable_amount == 0.00
    assert priced.lines[1].disposition == ClaimLineDisposition.DENIED
    assert priced.lines[1].denial_reason_code == "CO-97"


def test_timely_filing_denial(test_setup):
    router = test_setup["router"]
    contract = test_setup["contract"]
    policies = test_setup["policies"]

    claim = Claim(
        claim_id="TEST-TIMELY",
        claim_type=ClaimType.PROFESSIONAL,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="I10",
        filing_date="2026-07-01",  # > 90 days after Jan 15
        lines=[ClaimLine(line_number=1, procedure_code="99214", billed_amount=250.0, service_date="2026-01-15")],
        total_billed_amount=250.0,
    )
    priced = router.price_claim(claim, contract, policies)
    assert priced.total_allowable == 0.00
    assert priced.overall_disposition == ClaimLineDisposition.DENIED
    assert priced.lines[0].denial_reason_code == "CO-29"


def test_high_dollar_suspension(test_setup):
    router = test_setup["router"]
    contract = test_setup["contract"]
    policies = test_setup["policies"]

    claim = Claim(
        claim_id="TEST-HIGH-DOLLAR",
        claim_type=ClaimType.FACILITY,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-COMM-001",
        billing_provider_npi="1548291034",
        rendering_provider_npi="1548291034",
        principal_diagnosis="I21.09",
        lines=[ClaimLine(line_number=1, procedure_code="0001", revenue_code="0200", billed_amount=125000.0, drg_code="871")],
        total_billed_amount=125000.0,
    )
    priced = router.price_claim(claim, contract, policies)
    assert priced.total_allowable == 0.00
    assert priced.overall_disposition == ClaimLineDisposition.SUSPENDED
