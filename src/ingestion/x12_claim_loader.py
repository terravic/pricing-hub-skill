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

        # Handle raw X12 EDI text format (.x12 or .edi)
        if file_path.endswith((".x12", ".edi")):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
                raw_claims = self._parse_raw_x12_text(raw_text)
                for c in raw_claims:
                    is_valid, reason = validate_claim_scope(c)
                    if is_valid:
                        valid_claims.append(c)
                    else:
                        rejected.append({
                            "claim_id": c.claim_id,
                            "reason": reason,
                        })
                return valid_claims, rejected, errors
            except Exception as e:
                return [], [], [f"Failed to parse raw X12 file: {str(e)}"]

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

    def _parse_raw_x12_text(self, raw_text: str) -> List[Claim]:
        """Parses raw ANSI ASC X12 837 EDI format string into Claim objects."""
        claims: List[Claim] = []
        raw_text = raw_text.strip()
        if not raw_text:
            return claims

        # Detect segment delimiter (typically '~')
        seg_delim = "~" if "~" in raw_text else "\n"
        segments = [s.strip() for s in raw_text.split(seg_delim) if s.strip()]

        # Detect element delimiter (typically '*')
        elem_delim = "*"

        claim_id = "CLM-X12-RAW"
        claim_type = ClaimType.PROFESSIONAL
        lob = LineOfBusiness.COMMERCIAL
        member_id = "MEM-UNKNOWN"
        billing_npi = "0000000000"
        rendering_npi = "0000000000"
        principal_diag = "R05.9"
        drg_code = None
        total_billed = 0.0
        filing_date = "2026-02-01"
        service_date = "2026-01-15"
        lines: List[ClaimLine] = []

        for seg in segments:
            parts = seg.split(elem_delim)
            tag = parts[0].upper()

            if tag == "ST":
                # Detect claim type from ST03 version/flavor
                version = parts[3] if len(parts) > 3 else ""
                if "X223" in version:
                    claim_type = ClaimType.FACILITY
                elif "X224" in version:
                    claim_type = ClaimType.DENTAL
                elif "X222" in version:
                    claim_type = ClaimType.PROFESSIONAL

            elif tag == "NM1":
                role = parts[1] if len(parts) > 1 else ""
                if role == "41":  # Billing provider
                    if len(parts) > 9 and parts[9]:
                        billing_npi = parts[9]
                        rendering_npi = billing_npi
                elif role == "IL":  # Subscriber / Member
                    if len(parts) > 9 and parts[9]:
                        member_id = parts[9]
                        # Infer LOB from member prefix if available
                        if "MED" in member_id:
                            lob = LineOfBusiness.MEDICARE
                        elif "MCD" in member_id:
                            lob = LineOfBusiness.MEDICAID
                        elif "COMM" in member_id:
                            lob = LineOfBusiness.COMMERCIAL

            elif tag == "CLM":
                if len(parts) > 1:
                    claim_id = parts[1]
                if len(parts) > 2:
                    try:
                        total_billed = float(parts[2])
                    except ValueError:
                        total_billed = 0.0

            elif tag == "HI":
                # Diagnosis codes, e.g., HI*BK:I10*BF:E119*DR:470
                for diag_elem in parts[1:]:
                    if ":" in diag_elem:
                        qual, code = diag_elem.split(":", 1)
                        qual = qual.upper()
                        if qual in ("BK", "ABK"):
                            principal_diag = code
                        elif qual in ("DR", "ABF"):
                            drg_code = code

            elif tag == "DTP":
                qual = parts[1] if len(parts) > 1 else ""
                if qual in ("472", "435") and len(parts) > 3:
                    raw_dt = parts[3]
                    if len(raw_dt) == 8:
                        service_date = f"{raw_dt[:4]}-{raw_dt[4:6]}-{raw_dt[6:]}"

            elif tag == "SV1":
                # Professional service line: SV1*HC:99214*250.00*UN*1***1
                comp = parts[1].split(":") if len(parts) > 1 else []
                proc = comp[1] if len(comp) > 1 else "99214"
                mods = comp[2:] if len(comp) > 2 else []
                charge = float(parts[2]) if len(parts) > 2 else 0.0
                units = float(parts[4]) if len(parts) > 4 and parts[4] else 1.0

                lines.append(ClaimLine(
                    line_number=len(lines) + 1,
                    procedure_code=proc,
                    billed_amount=charge,
                    units=units,
                    modifiers=mods,
                    service_date=service_date,
                ))

            elif tag == "SV2":
                # Facility service line: SV2*0110*HC:0001*35000.00*UN*4
                rev_code = parts[1] if len(parts) > 1 else "0110"
                comp = parts[2].split(":") if len(parts) > 2 else []
                proc = comp[1] if len(comp) > 1 else "0001"
                charge = float(parts[3]) if len(parts) > 3 else 0.0
                units = float(parts[5]) if len(parts) > 5 and parts[5] else 1.0

                lines.append(ClaimLine(
                    line_number=len(lines) + 1,
                    procedure_code=proc,
                    billed_amount=charge,
                    units=units,
                    revenue_code=rev_code,
                    drg_code=drg_code,
                    service_date=service_date,
                ))

            elif tag == "SV3":
                # Dental service line: SV3*AD:D0120*85.00**1
                claim_type = ClaimType.DENTAL
                comp = parts[1].split(":") if len(parts) > 1 else []
                proc = comp[1] if len(comp) > 1 else "D0120"
                charge = float(parts[2]) if len(parts) > 2 else 0.0
                lines.append(ClaimLine(
                    line_number=len(lines) + 1,
                    procedure_code=proc,
                    billed_amount=charge,
                    units=1.0,
                    service_date=service_date,
                ))

        claim = Claim(
            claim_id=claim_id,
            claim_type=claim_type,
            line_of_business=lob,
            member_id=member_id,
            billing_provider_npi=billing_npi,
            rendering_provider_npi=rendering_npi,
            principal_diagnosis=principal_diag,
            lines=lines,
            total_billed_amount=total_billed,
            filing_date=filing_date,
            metadata={"drg_code": drg_code} if drg_code else {},
        )
        claims.append(claim)
        return claims
