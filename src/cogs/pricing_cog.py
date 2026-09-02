"""Pricing Engine Cog & Handshake Simulator."""

from typing import Dict, Any, Optional
from src.ingestion.contract_parser import ContractParser
from src.ingestion.policy_parser import PolicyParser
from src.pricing_engine.pricing_router import PricingRouter
from src.models.claim_models import Claim, ClaimLine, ClaimType, LineOfBusiness


class PricingEngineCog:
    """Inter-cog pricing execution component that receives inputs from Member, Benefit, and Contract Cogs."""

    def __init__(self, contract_parser: ContractParser, policy_parser: PolicyParser):
        self.contract_parser = contract_parser
        self.policy_parser = policy_parser
        self.router = PricingRouter()

    def execute_pricing(
        self,
        claim_id: str,
        member_context: Dict[str, Any],
        benefit_context: Dict[str, Any],
        contract_context: Dict[str, Any],
        line_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Runs the pricing engine given inter-cog upstream inputs."""
        contract = self.contract_parser.get_contract_by_id(contract_context["resolved_contract_id"])
        if not contract:
            raise ValueError(f"Contract {contract_context['resolved_contract_id']} not found.")

        # Build claim
        lob = LineOfBusiness(member_context["line_of_business"])
        proc_code = line_data.get("procedure_code", "0001")
        drg_code = line_data.get("drg_code")
        billed = float(line_data.get("billed_amount", 0.0))

        claim_type = ClaimType.FACILITY if drg_code else ClaimType.PROFESSIONAL

        line = ClaimLine(
            line_number=1,
            procedure_code=proc_code,
            billed_amount=billed,
            units=1.0,
            drg_code=drg_code,
            revenue_code="0110" if drg_code else None,
        )

        claim = Claim(
            claim_id=claim_id,
            claim_type=claim_type,
            line_of_business=lob,
            member_id=member_context["member_id"],
            billing_provider_npi=contract_context["provider_npi"],
            rendering_provider_npi=contract_context["provider_npi"],
            principal_diagnosis="M16.11" if drg_code else "M23.22",
            lines=[line],
            total_billed_amount=billed,
        )

        policies = list(self.policy_parser.policies.values())
        priced = self.router.price_claim(claim, contract, policies)

        return {
            "claim_id": claim_id,
            "calculated_allowable": priced.total_allowable,
            "overall_disposition": priced.overall_disposition.value,
            "contract_citations": priced.lines[0].contract_citations if priced.lines else [],
            "policy_citations": priced.lines[0].policy_citations if priced.lines else [],
            "audit_trail": priced.lines[0].audit_trail if priced.lines else [],
        }
