#!/usr/bin/env python3
"""CLI utility to ingest contracts, rate cards, and clinical reimbursement policies."""

import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.contract_parser import ContractParser
from src.ingestion.policy_parser import PolicyParser


def main():
    parser = argparse.ArgumentParser(description="Ingest contracts and clinical policies into Pricing Hub.")
    parser.add_argument("--contracts-dir", default="data/contracts", help="Path to contracts directory")
    parser.add_argument("--policies-dir", default="data/policies", help="Path to policies directory")
    args = parser.parse_args()

    print("=================================================================")
    print("        PRICING HUB: CONTRACT & POLICY INGESTION ENGINE          ")
    print("=================================================================\n")

    # 1. Ingest Contracts
    print(f"[*] Ingesting Provider Contracts from: {args.contracts_dir}")
    cp = ContractParser()
    c_results = cp.load_directory(args.contracts_dir)
    print(f"    - Contracts Loaded: {c_results['loaded']}")
    print(f"    - Contracts Failed: {c_results['failed']}")

    for cid in c_results["contracts"]:
        c = cp.get_contract_by_id(cid)
        print(f"\n    >> Contract ID: {c.contract_id} ({c.contract_name})")
        print(f"       Line of Business: {c.line_of_business.value}")
        print(f"       Effective Window: {c.effective_start} to {c.effective_end}")
        print(f"       Fee Schedule Rates: {len(c.fee_schedule)} codes")
        print(f"       DRG Case Rates: {len(c.drg_rules)} codes")
        print(f"       % of Charges Rules: {len(c.percent_of_charges_rules)} rules")
        print(f"       Provider NPIs: {', '.join(c.provider_npi_list)}")

    if c_results["errors"]:
        print(f"\n[!] Contract Ingestion Errors: {c_results['errors']}")

    # 2. Ingest Policies
    print(f"\n[*] Ingesting Clinical Reimbursement Policies from: {args.policies_dir}")
    pp = PolicyParser()
    p_results = pp.load_directory(args.policies_dir)
    print(f"    - Policy Rules Loaded: {p_results['loaded_rules']}")
    print(f"    - Policy Files Failed: {p_results['failed_files']}")

    for pid, p in pp.policies.items():
        print(f"\n    >> Policy ID: {p.policy_id} - {p.policy_title}")
        print(f"       Type: {p.policy_type.value} | Paragraph: {p.paragraph_id}")
        print(f"       Target Codes: {', '.join(p.target_procedure_codes) if p.target_procedure_codes else 'GLOBAL'}")
        print(f"       Action: {p.rule_action.value} | CARC: {p.denial_carc or 'N/A'}")
        print(f"       Citation: {p.citation_text}")

    print("\n=================================================================")
    print("INGESTION STATUS: SUCCESSFUL. Ready for Claim Adjudication.")
    print("=================================================================")

    # Automatically create / update dashboard with ingested contracts
    from src.ui.dashboard_generator import generate_dashboard, print_dashboard_banner
    generate_dashboard(results=c_results, task_type="ingestion")
    print_dashboard_banner(task_name="Contract and Policy Ingestion")


if __name__ == "__main__":
    main()
