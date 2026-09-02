"""Contract and Rate Card Ingestion Parser."""

import json
import os
from typing import Dict, List, Any, Tuple, Optional
import yaml
from src.models.contract_models import ContractRateCard, DRGRule, PercentOfChargesRule, MPPRRule
from src.models.claim_models import LineOfBusiness


class ContractParser:
    """Parses and normalizes provider contracts, fee schedules, and rate cards."""

    def __init__(self):
        self.contracts: Dict[str, ContractRateCard] = {}
        self.provider_contract_index: Dict[str, str] = {}  # NPI -> Contract ID

    def parse_file(self, file_path: str) -> Tuple[Optional[ContractRateCard], List[str]]:
        """Parses a contract file (JSON or YAML) and validates its schema and rate logic."""
        errors: List[str] = []
        if not os.path.exists(file_path):
            return None, [f"Contract file not found: {file_path}"]

        try:
            if file_path.endswith(".pdf"):
                return self.parse_pdf_contract(file_path)
            elif file_path.endswith(".yaml") or file_path.endswith(".yml"):
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
            else:
                with open(file_path, "r") as f:
                    data = json.load(f)
        except Exception as e:
            return None, [f"Failed to parse file syntax: {str(e)}"]

        # Validate mandatory fields
        required_fields = ["contract_id", "contract_name", "line_of_business", "effective_start", "effective_end"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing mandatory field: '{field}'")

        if errors:
            return None, errors

        # Validate LOB
        try:
            lob = LineOfBusiness(data["line_of_business"])
        except ValueError:
            errors.append(f"Invalid Line of Business: '{data['line_of_business']}'")
            return None, errors

        # Validate Rate sanity
        fee_schedule = data.get("fee_schedule", {})
        for code, rate in fee_schedule.items():
            if rate < 0:
                errors.append(f"Negative rate encountered for CPT/HCPCS {code}: {rate}")

        drg_rules = {}
        for code, drg_data in data.get("drg_rules", {}).items():
            if drg_data.get("base_rate", 0) <= 0:
                errors.append(f"Invalid DRG base rate for {code}: {drg_data.get('base_rate')}")
            drg_rules[code] = DRGRule(**drg_data)

        poc_rules = [
            PercentOfChargesRule(**r)
            for r in data.get("percent_of_charges_rules", [])
        ]

        card = ContractRateCard(
            contract_id=data["contract_id"],
            contract_name=data["contract_name"],
            line_of_business=lob,
            provider_npi_list=data.get("provider_npi_list", []),
            effective_start=data["effective_start"],
            effective_end=data["effective_end"],
            fee_schedule=fee_schedule,
            drg_rules=drg_rules,
            percent_of_charges_rules=poc_rules,
            per_diem_rates=data.get("per_diem_rates", {}),
            mppr_rule=MPPRRule(),
            contract_clauses=data.get("contract_clauses", {}),
        )

        # Store in internal index
        self.contracts[card.contract_id] = card
        for npi in card.provider_npi_list:
            self.provider_contract_index[npi] = card.contract_id

        # Auto-generate / adapt dashboard for ingestion task
        try:
            from src.ui.dashboard_generator import generate_dashboard
            generate_dashboard(task_type="ingestion")
        except Exception:
            pass

        return card, errors

    def parse_pdf_contract(self, file_path: str) -> Tuple[Optional[ContractRateCard], List[str]]:
        """Extracts contract text and rate schedules from a PDF contract document."""
        import pypdf
        errors: List[str] = []
        try:
            reader = pypdf.PdfReader(file_path)
            full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            return None, [f"Failed to read PDF file: {str(e)}"]

        # If a companion JSON rate card exists, bind it with the PDF clauses
        json_companion = file_path.replace(".pdf", ".json")
        if os.path.exists(json_companion):
            card, errs = self.parse_file(json_companion)
            if card:
                card.contract_clauses["PDF_DOCUMENT_SOURCE"] = os.path.basename(file_path)
                return card, errs

        return None, ["PDF parsed as document reference; structured rate card loaded from JSON."]

    def load_directory(self, dir_path: str) -> Dict[str, Any]:
        """Loads and indexes all contract files in a directory."""
        results = {"loaded": 0, "failed": 0, "contracts": [], "errors": {}}
        if not os.path.exists(dir_path):
            results["errors"]["dir"] = [f"Directory does not exist: {dir_path}"]
            return results

        for filename in sorted(os.listdir(dir_path)):
            if filename.endswith(".json") or filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(dir_path, filename)
                contract, errs = self.parse_file(filepath)
                if contract and not errs:
                    results["loaded"] += 1
                    results["contracts"].append(contract.contract_id)
                else:
                    results["failed"] += 1
                    results["errors"][filename] = errs

        return results

    def get_contract_by_id(self, contract_id: str) -> Optional[ContractRateCard]:
        return self.contracts.get(contract_id)

    def get_contract_for_provider(self, provider_npi: str, lob: Optional[LineOfBusiness] = None) -> Optional[ContractRateCard]:
        """Resolves active contract for provider NPI and optional line of business."""
        contract_id = self.provider_contract_index.get(provider_npi)
        if contract_id:
            contract = self.contracts.get(contract_id)
            if lob is None or contract.line_of_business == lob:
                return contract

        # Fallback: scan all contracts if provider participates across multiple LOBs
        for c in self.contracts.values():
            if provider_npi in c.provider_npi_list:
                if lob is None or c.line_of_business == lob:
                    return c
        return None
