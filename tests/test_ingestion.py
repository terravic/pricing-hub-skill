"""Tests for Contract, Policy, and Claim Ingestion Subsystem."""

import pytest
from src.ingestion.contract_parser import ContractParser
from src.ingestion.policy_parser import PolicyParser
from src.ingestion.x12_claim_loader import X12ClaimLoader
from src.models.claim_models import Claim, ClaimLine, ClaimType, LineOfBusiness


def test_contract_ingestion_valid():
    parser = ContractParser()
    res = parser.load_directory("data/contracts")
    assert res["loaded"] == 3
    assert res["failed"] == 0
    assert "CTR-COMM-2026" in res["contracts"]
    assert "CTR-MED-ADV-2026" in res["contracts"]
    assert "CTR-MCD-MCO-2026" in res["contracts"]

    comm = parser.get_contract_by_id("CTR-COMM-2026")
    assert comm is not None
    assert comm.fee_schedule["99214"] == 165.00
    assert "470" in comm.drg_rules
    assert comm.drg_rules["470"].base_rate == 10500.00


def test_policy_ingestion_valid():
    parser = PolicyParser()
    res = parser.load_directory("data/policies")
    assert res["loaded_rules"] >= 6
    assert res["failed_files"] == 0

    mppr_pol = parser.get_policy("PAYER-RP-042")
    assert mppr_pol is not None
    assert mppr_pol.paragraph_id == "Paragraph 4.1"
    assert "29881" in mppr_pol.target_procedure_codes

    cardiac_rules = parser.get_rules_for_procedure("93000")
    assert len(cardiac_rules) >= 1
    assert cardiac_rules[0].policy_id == "CMS-NCD-220.4"


def test_scope_enforcement_accepts_supported_claims():
    loader = X12ClaimLoader()
    valid_claim = Claim(
        claim_id="CLM-VALID-01",
        claim_type=ClaimType.PROFESSIONAL,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="I10",
        lines=[ClaimLine(line_number=1, procedure_code="99214", billed_amount=250.0)],
        total_billed_amount=250.0,
    )
    claim, err = loader.load_claim_from_dict(valid_claim.to_dict())
    assert claim is not None
    assert err is None


def test_scope_enforcement_rejects_dental_vision_pharmacy():
    loader = X12ClaimLoader()

    # Dental
    dental = Claim(
        claim_id="CLM-DENT-01",
        claim_type=ClaimType.DENTAL,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="K02.9",
        lines=[ClaimLine(line_number=1, procedure_code="D0120", billed_amount=80.0)],
        total_billed_amount=80.0,
    )
    c_dent, err_dent = loader.load_claim_from_dict(dental.to_dict())
    assert c_dent is None
    assert "REJECT_UNSUPPORTED_LOB_EXCLUSION" in err_dent
    assert "DENTAL" in err_dent

    # Vision
    vision = Claim(
        claim_id="CLM-VIS-01",
        claim_type=ClaimType.VISION,
        line_of_business=LineOfBusiness.COMMERCIAL,
        member_id="MEM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="H52.1",
        lines=[ClaimLine(line_number=1, procedure_code="V2020", billed_amount=150.0)],
        total_billed_amount=150.0,
    )
    c_vis, err_vis = loader.load_claim_from_dict(vision.to_dict())
    assert c_vis is None
    assert "REJECT_UNSUPPORTED_LOB_EXCLUSION" in err_vis

    # Pharmacy
    pharm = Claim(
        claim_id="CLM-RX-01",
        claim_type=ClaimType.PHARMACY,
        line_of_business=LineOfBusiness.MEDICARE,
        member_id="MEM-001",
        billing_provider_npi="1982730192",
        rendering_provider_npi="1982730192",
        principal_diagnosis="E11.9",
        lines=[ClaimLine(line_number=1, procedure_code="0002458", billed_amount=45.0)],
        total_billed_amount=45.0,
    )
    c_rx, err_rx = loader.load_claim_from_dict(pharm.to_dict())
    assert c_rx is None
    assert "REJECT_UNSUPPORTED_LOB_EXCLUSION" in err_rx


def test_contract_pdf_parsing():
    parser = ContractParser()
    card, errs = parser.parse_file("data/contracts/commercial_provider_contract.pdf")
    assert card is not None
    assert card.contract_id == "CTR-COMM-2026"
    assert card.fee_schedule["99214"] == 165.00
    assert "commercial_provider_contract.pdf" in card.contract_clauses.get("PDF_DOCUMENT_SOURCE", "")


def test_x12_to_json_loop_structure_loading():
    loader = X12ClaimLoader()
    claims, rejected, errs = loader.load_claims_file("data/claims_x12/sample_parsed_x12_loops.json")
    assert len(claims) == 1
    c = claims[0]
    assert c.claim_id == "CLM-X12-PARSED-001"
    assert c.claim_type == ClaimType.PROFESSIONAL
    assert c.line_of_business == LineOfBusiness.COMMERCIAL
    assert c.member_id == "MEM-COMM-001"
    assert c.lines[0].procedure_code == "99214"
    assert c.lines[0].billed_amount == 250.00


def test_combined_integration_matrix_columns():
    import csv
    with open("data/integration_tests/cog_integration_test_file.csv", "r") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        assert "member_id" in headers
        assert "provider_id" in headers
        assert "service_type" in headers
        assert "service_date" in headers
        assert "pricing_methodology" in headers
        assert "expected_allowable" in headers
        rows = list(reader)
        assert len(rows) >= 5


def test_single_raw_837p_x12_file_ingestion():
    loader = X12ClaimLoader()
    claims, rejected, errs = loader.load_claims_file("data/claims_x12/sample_837p_professional.x12")
    assert len(errs) == 0
    assert len(rejected) == 0
    assert len(claims) == 1
    c = claims[0]
    assert c.claim_id == "CLM-COMM-PROF-001"
    assert c.claim_type == ClaimType.PROFESSIONAL
    assert c.billing_provider_npi == "1982730192"
    assert c.member_id == "MEM-COMM-001"
    assert c.total_billed_amount == 250.00
    assert len(c.lines) == 1
    assert c.lines[0].procedure_code == "99214"
    assert c.lines[0].billed_amount == 250.00


def test_single_raw_837i_x12_file_ingestion():
    loader = X12ClaimLoader()
    claims, rejected, errs = loader.load_claims_file("data/claims_x12/sample_837i_facility.x12")
    assert len(errs) == 0
    assert len(rejected) == 0
    assert len(claims) == 1
    c = claims[0]
    assert c.claim_id == "CLM-COMM-FAC-026"
    assert c.claim_type == ClaimType.FACILITY
    assert c.billing_provider_npi == "1548291034"
    assert c.total_billed_amount == 35000.00
    assert len(c.lines) == 1
    assert c.lines[0].revenue_code == "0110"


def test_single_raw_837d_x12_file_rejection():
    loader = X12ClaimLoader()
    claims, rejected, errs = loader.load_claims_file("data/claims_x12/sample_837d_dental_excluded.x12")
    assert len(claims) == 0
    assert len(rejected) == 1
    assert rejected[0]["claim_id"] == "CLM-DENT-EXCLUDED-01"
    assert "REJECT_UNSUPPORTED_LOB_EXCLUSION" in rejected[0]["reason"]
    assert "DENTAL" in rejected[0]["reason"]

