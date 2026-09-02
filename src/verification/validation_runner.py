"""Batch Claim Validation Runner for Parity and Concordance Measurement."""

import os
import json
import time
from typing import Dict, List, Any, Optional
from src.ingestion.contract_parser import ContractParser
from src.ingestion.policy_parser import PolicyParser
from src.ingestion.x12_claim_loader import X12ClaimLoader
from src.pricing_engine.pricing_router import PricingRouter
from src.verification.discrepancy_detector import DiscrepancyDetector
from src.verification.audit_log_generator import AuditLogGenerator
from src.models.pricing_models import ClaimDiscrepancy


class ValidationRunner:
    """Orchestrates end-to-end allowable verification across golden datasets and trial batches."""

    def __init__(
        self,
        contracts_dir: str = "data/contracts",
        policies_dir: str = "data/policies",
        allowable_tolerance: float = 0.01,
    ):
        self.contract_parser = ContractParser()
        self.contract_parser.load_directory(contracts_dir)

        self.policy_parser = PolicyParser()
        self.policy_parser.load_directory(policies_dir)

        self.claim_loader = X12ClaimLoader()
        self.router = PricingRouter()
        self.detector = DiscrepancyDetector(allowable_tolerance=allowable_tolerance)
        self.audit_gen = AuditLogGenerator()

    def run_validation(self, claims_file_path: str) -> Dict[str, Any]:
        """Runs batch verification against a claims dataset containing ground-truth expectations."""
        start_time = time.time()
        with open(claims_file_path, "r") as f:
            raw_claims = json.load(f)

        if isinstance(raw_claims, dict):
            raw_claims = [raw_claims]

        total_claims = len(raw_claims)
        passed_claims = 0
        failed_claims = 0
        all_discrepancies: List[ClaimDiscrepancy] = []
        total_billed = 0.0
        total_allowable = 0.0

        for raw in raw_claims:
            claim, err = self.claim_loader.load_claim_from_dict(raw)
            if not claim:
                failed_claims += 1
                all_discrepancies.append(ClaimDiscrepancy(
                    claim_id=raw.get("claim_id", "UNKNOWN"),
                    line_number=0,
                    discrepancy_type="SCOPE_REJECTION",
                    expected_allowable=0.0,
                    calculated_allowable=0.0,
                    variance_amount=0.0,
                    variance_percentage=0.0,
                    expected_disposition="REJECTED",
                    calculated_disposition="REJECTED",
                    root_cause=f"Scope rejection: {err}",
                ))
                continue

            # Resolve matching contract
            contract = self.contract_parser.get_contract_for_provider(
                claim.billing_provider_npi,
                lob=claim.line_of_business,
            )
            if not contract:
                # Fallback to LOB default contract
                for c in self.contract_parser.contracts.values():
                    if c.line_of_business == claim.line_of_business:
                        contract = c
                        break

            if not contract:
                failed_claims += 1
                continue

            # Price claim
            policies = list(self.policy_parser.policies.values())
            priced = self.router.price_claim(claim, contract, policies)

            total_billed += priced.total_billed
            total_allowable += priced.total_allowable

            # Check discrepancies against ground truth
            discrepancies = self.detector.compare_claim(priced, raw)
            if not discrepancies:
                passed_claims += 1
            else:
                failed_claims += 1
                all_discrepancies.extend(discrepancies)

        concordance_rate = round((passed_claims / total_claims * 100.0) if total_claims > 0 else 0.0, 2)
        elapsed_sec = round(time.time() - start_time, 3)

        return {
            "total_claims": total_claims,
            "passed_claims": passed_claims,
            "failed_claims": failed_claims,
            "concordance_rate": concordance_rate,
            "total_billed": round(total_billed, 2),
            "total_allowable": round(total_allowable, 2),
            "total_discrepancies": len(all_discrepancies),
            "discrepancies": [d.to_dict() for d in all_discrepancies],
            "elapsed_seconds": elapsed_sec,
        }
