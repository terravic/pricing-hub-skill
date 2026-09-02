"""Claim Ingestion Loader with X12 Interoperability and Scope Enforcement Gate."""

import json
import os
from typing import Dict, List, Any, Tuple, Optional
from src.models.claim_models import (
    Claim,
    ClaimLine,
    ClaimType,
    LineOfBusiness,
    validate_claim_scope,
)


class X12ClaimLoader:
    """Loads claims from direct JSON or from x12-to-json-parser output structures,
    enforcing scope constraints (Commercial, Medicare, Medicaid / Professional & Facility).
    Excludes Vision, Dental, Pharmacy.
    """

    def __init__(self):
        self.scope_rejected_claims: List[Dict[str, Any]] = []

    def load_claim_from_dict(self, data: Dict[str, Any]) -> Tuple[Optional[Claim], Optional[str]]:
        """Parses a dictionary into a Claim object and runs scope validation."""
        # Detect if this is an x12-to-json raw structure or a pre-normalized claim dict
        if "interchange" in data or "functional_groups" in data or "loop_2300" in data:
            claim = self._parse_x12_json_loops(data)
        else:
            claim = Claim.from_dict(data)

        # Enforce scope boundaries
        is_valid, reason = validate_claim_scope(claim)
        if not is_valid:
            self.scope_rejected_claims.append({
                "claim_id": claim.claim_id,
                "claim_type": claim.claim_type.value,
                "line_of_business": claim.line_of_business.value,
                "rejection_reason": reason,
            })
            return None, reason

        return claim, None

    def load_claims_file(self, file_path: str) -> Tuple[List[Claim], List[Dict[str, Any]], List[str]]:
        """Loads a claims JSON file containing a claim or list of claims.
        Returns: (valid_claims, rejected_claims, errors)
        """
        valid_claims: List[Claim] = []
        rejected: List[Dict[str, Any]] = []
        errors: List[str] = []

        if not os.path.exists(file_path):
            return [], [], [f"Claim file not found: {file_path}"]

        try:
            with open(file_path, "r") as f:
                content = json.load(f)
        except Exception as e:
            return [], [], [f"Failed to read claim JSON: {str(e)}"]

        if isinstance(content, dict):
            content = [content]

        for item in content:
            try:
                claim, err = self.load_claim_from_dict(item)
                if claim:
                    valid_claims.append(claim)
                else:
                    rejected.append({
                        "claim_id": item.get("claim_id", "UNKNOWN"),
                        "reason": err,
                    })
            except Exception as e:
                errors.append(f"Failed to parse claim {item.get('claim_id')}: {str(e)}")

        return valid_claims, rejected, errors

    def _parse_x12_json_loops(self, x12_data: Dict[str, Any]) -> Claim:
        """Transforms x12-to-json-parser hierarchical loop segments into normalized Claim."""
        # Extract Loop 2300 (Claim Information)
        l2300 = x12_data.get("loop_2300", {})
        claim_id = l2300.get("claim_id") or l2300.get("clm_01", "CLM-X12-001")
        total_billed = float(l2300.get("total_charge_amount") or l2300.get("clm_02", 0.0))

        # Detect Claim Type from CLM-05 or loop structure
        claim_type_raw = str(x12_data.get("claim_type", "")).upper()
        if "FACILITY" in claim_type_raw or "837I" in claim_type_raw:
            claim_type = ClaimType.FACILITY
        elif "DENTAL" in claim_type_raw or "837D" in claim_type_raw:
            claim_type = ClaimType.DENTAL
        elif "PHARMACY" in claim_type_raw or "NCPDP" in claim_type_raw:
            claim_type = ClaimType.PHARMACY
        elif "VISION" in claim_type_raw:
            claim_type = ClaimType.VISION
        else:
            claim_type = ClaimType.PROFESSIONAL

        # Line of business
        lob_raw = str(x12_data.get("line_of_business", "COMMERCIAL")).upper()
        try:
            lob = LineOfBusiness(lob_raw)
        except ValueError:
            lob = LineOfBusiness.COMMERCIAL

        member_id = x12_data.get("member_id") or x12_data.get("loop_2010ba", {}).get("subscriber_id", "MEM-000")
        billing_npi = x12_data.get("billing_provider_npi") or x12_data.get("loop_2010aa", {}).get("npi", "0000000000")
        rendering_npi = x12_data.get("rendering_provider_npi") or billing_npi

        principal_diag = l2300.get("principal_diagnosis", "R05.9")

        # Parse Loop 2400 (Service Lines)
        lines: List[ClaimLine] = []
        l2400_list = x12_data.get("loop_2400", [])
        for idx, l2400 in enumerate(l2400_list, start=1):
            sv1 = l2400.get("sv1", {})
            sv2 = l2400.get("sv2", {})
            proc = sv1.get("procedure_code") or sv2.get("procedure_code") or "99214"
            billed = float(sv1.get("charge_amount") or sv2.get("charge_amount") or 0.0)
            units = float(sv1.get("units") or sv2.get("units") or 1.0)
            rev_code = sv2.get("revenue_code")
            modifiers = sv1.get("modifiers") or []

            lines.append(ClaimLine(
                line_number=idx,
                procedure_code=proc,
                billed_amount=billed,
                units=units,
                revenue_code=rev_code,
                modifiers=modifiers,
                service_date=l2400.get("service_date", "2026-01-15"),
            ))

        return Claim(
            claim_id=claim_id,
            claim_type=claim_type,
            line_of_business=lob,
            member_id=member_id,
            billing_provider_npi=billing_npi,
            rendering_provider_npi=rendering_npi,
            principal_diagnosis=principal_diag,
            lines=lines,
            total_billed_amount=total_billed,
            filing_date=x12_data.get("filing_date", "2026-02-01"),
        )
