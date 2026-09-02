"""Contract Pick Cog Simulator."""

from typing import Dict, Any, Optional
from src.ingestion.contract_parser import ContractParser
from src.models.claim_models import LineOfBusiness


class ContractPickCog:
    """Matches billing/rendering provider NPI to active contracted rate schedules."""

    def __init__(self, contract_parser: ContractParser):
        self.contract_parser = contract_parser

    def resolve_contract(self, provider_npi: str, lob_str: str) -> Optional[Dict[str, Any]]:
        try:
            lob = LineOfBusiness(lob_str)
        except ValueError:
            return None

        contract = self.contract_parser.get_contract_for_provider(provider_npi, lob=lob)
        if not contract:
            return None

        primary_methodology = "FEE_SCHEDULE"
        if contract.drg_rules:
            primary_methodology = "DRG_CASE_RATE"

        return {
            "provider_npi": provider_npi,
            "resolved_contract_id": contract.contract_id,
            "contract_name": contract.contract_name,
            "effective_start": contract.effective_start,
            "effective_end": contract.effective_end,
            "pricing_methodology": primary_methodology,
        }
