"""Tests for Inter-Cog Pipeline Interactions and Handshakes."""

import pytest
from src.ingestion.contract_parser import ContractParser
from src.ingestion.policy_parser import PolicyParser
from src.cogs.member_cog import MemberPickCog
from src.cogs.benefit_cog import BenefitAccumulatorCog
from src.cogs.contract_cog import ContractPickCog
from src.cogs.pricing_cog import PricingEngineCog


@pytest.fixture
def cog_pipeline():
    cp = ContractParser()
    cp.load_directory("data/contracts")

    pp = PolicyParser()
    pp.load_directory("data/policies")

    mem_cog = MemberPickCog("data/benefits/member_benefits_accumulators.json")
    ben_cog = BenefitAccumulatorCog("data/benefits/member_benefits_accumulators.json")
    ctr_cog = ContractPickCog(cp)
    pri_cog = PricingEngineCog(cp, pp)

    return {
        "member_cog": mem_cog,
        "benefit_cog": ben_cog,
        "contract_cog": ctr_cog,
        "pricing_cog": pri_cog,
    }


def test_cog_handshake_commercial_arthroscopy(cog_pipeline):
    mem_cog = cog_pipeline["member_cog"]
    ben_cog = cog_pipeline["benefit_cog"]
    ctr_cog = cog_pipeline["contract_cog"]
    pri_cog = cog_pipeline["pricing_cog"]

    # 1. Member Cog
    m_ctx = mem_cog.resolve_member("MEM-COMM-001")
    assert m_ctx is not None
    assert m_ctx["line_of_business"] == "COMMERCIAL"

    # 2. Benefit Cog
    b_ctx = ben_cog.evaluate_benefits("MEM-COMM-001")
    assert b_ctx is not None
    assert b_ctx["deductible_remaining"] == 500.00
    assert b_ctx["in_network_tier"] == "TIER_1"

    # 3. Contract Cog
    c_ctx = ctr_cog.resolve_contract("1982730192", m_ctx["line_of_business"])
    assert c_ctx is not None
    assert c_ctx["resolved_contract_id"] == "CTR-COMM-2026"

    # 4. Pricing Cog
    res = pri_cog.execute_pricing(
        claim_id="COG-TEST-001",
        member_context=m_ctx,
        benefit_context=b_ctx,
        contract_context=c_ctx,
        line_data={"procedure_code": "29881", "billed_amount": 3500.00},
    )
    assert res["calculated_allowable"] == 1250.00
    assert res["overall_disposition"] == "PAID"
    assert len(res["contract_citations"]) >= 1


def test_cog_handshake_medicare_drg(cog_pipeline):
    mem_cog = cog_pipeline["member_cog"]
    ben_cog = cog_pipeline["benefit_cog"]
    ctr_cog = cog_pipeline["contract_cog"]
    pri_cog = cog_pipeline["pricing_cog"]

    # 1. Member Cog
    m_ctx = mem_cog.resolve_member("MEM-MED-042")
    assert m_ctx is not None
    assert m_ctx["line_of_business"] == "MEDICARE"

    # 2. Benefit Cog
    b_ctx = ben_cog.evaluate_benefits("MEM-MED-042")
    assert b_ctx["deductible_remaining"] == 0.00

    # 3. Contract Cog
    c_ctx = ctr_cog.resolve_contract("1649201948", m_ctx["line_of_business"])
    assert c_ctx is not None
    assert c_ctx["resolved_contract_id"] == "CTR-MED-ADV-2026"

    # 4. Pricing Cog
    res = pri_cog.execute_pricing(
        claim_id="COG-TEST-002",
        member_context=m_ctx,
        benefit_context=b_ctx,
        contract_context=c_ctx,
        line_data={"drg_code": "470", "billed_amount": 25000.00},
    )
    assert res["calculated_allowable"] == 14040.00  # 7200 * 1.95
    assert res["overall_disposition"] == "PAID"
