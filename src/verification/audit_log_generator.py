"""Chain-of-Thought Audit Log Generator with Policy Paragraph Citations."""

import json
from typing import Dict, Any, List
from src.models.claim_models import Claim
from src.models.pricing_models import PricedClaim


class AuditLogGenerator:
    """Generates human-readable and machine-verifiable Chain-of-Thought audit logs."""

    def generate_claim_audit_trail(self, claim: Claim, priced: PricedClaim) -> Dict[str, Any]:
        """Assembles a comprehensive audit record for an adjudicated claim."""
        lines_audit = []
        for pl in priced.lines:
            line_record = {
                "line_number": pl.line_number,
                "procedure_code": pl.procedure_code,
                "billed_charge": f"${pl.billed_amount:,.2f}",
                "allowable_amount": f"${pl.allowable_amount:,.2f}",
                "pricing_methodology": pl.pricing_methodology.value,
                "disposition": pl.disposition.value,
                "denial_carc": pl.denial_reason_code,
                "denial_description": pl.denial_reason_description,
                "contract_citations": pl.contract_citations,
                "policy_citations": pl.policy_citations,
                "calculation_reasoning": pl.audit_trail,
            }
            lines_audit.append(line_record)

        audit_doc = {
            "claim_id": claim.claim_id,
            "line_of_business": claim.line_of_business.value,
            "claim_type": claim.claim_type.value,
            "member_id": claim.member_id,
            "billing_provider_npi": claim.billing_provider_npi,
            "contract_id": priced.contract_id,
            "principal_diagnosis": claim.principal_diagnosis,
            "adjudication_timestamp": priced.adjudication_timestamp,
            "summary": {
                "total_billed": f"${priced.total_billed:,.2f}",
                "total_allowable": f"${priced.total_allowable:,.2f}",
                "contractual_adjustment": f"${priced.total_billed - priced.total_allowable:,.2f}",
                "overall_disposition": priced.overall_disposition.value,
                "execution_time_ms": f"{priced.execution_time_ms} ms",
            },
            "line_item_audit": lines_audit,
        }
        return audit_doc

    def format_markdown_report(self, audit_doc: Dict[str, Any]) -> str:
        """Formats an audit document into clean Markdown for presentation or logging."""
        md = []
        md.append(f"### Claim Adjudication Audit Report: `{audit_doc['claim_id']}`")
        md.append(f"- **Line of Business**: {audit_doc['line_of_business']} | **Type**: {audit_doc['claim_type']}")
        md.append(f"- **Member ID**: `{audit_doc['member_id']}` | **Contract ID**: `{audit_doc['contract_id']}`")
        md.append(f"- **Financial Summary**: Billed: **{audit_doc['summary']['total_billed']}** | Allowable: **{audit_doc['summary']['total_allowable']}** | Disposition: **`{audit_doc['summary']['overall_disposition']}`**\n")
        md.append("| Line | CPT/Rev | Billed | Allowable | Method | Disp | Policy / Contract Citations |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        for l in audit_doc["line_item_audit"]:
            cits = "; ".join(l["policy_citations"] + l["contract_citations"])
            if not cits:
                cits = "N/A"
            md.append(f"| {l['line_number']} | {l['procedure_code']} | {l['billed_charge']} | {l['allowable_amount']} | {l['pricing_methodology']} | {l['disposition']} | {cits} |")

        md.append("\n**Chain of Thought Adjudication Steps:**")
        for l in audit_doc["line_item_audit"]:
            md.append(f"- **Line {l['line_number']} ({l['procedure_code']})**: " + " | ".join(l["calculation_reasoning"]))

        return "\n".join(md)
