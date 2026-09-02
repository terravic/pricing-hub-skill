#!/usr/bin/env python3
"""CLI utility to execute automated allowable amount verification and generate Chain-of-Thought audit trails."""

import sys
import os
import argparse
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.verification.validation_runner import ValidationRunner
from src.verification.audit_log_generator import AuditLogGenerator


def main():
    parser = argparse.ArgumentParser(description="Run Automated Allowable Amount Verification on claims.")
    parser.add_argument("--claims-file", default="data/golden_dataset/golden_claims_all.json", help="Path to claims dataset")
    parser.add_argument("--contracts-dir", default="data/contracts", help="Path to contracts directory")
    parser.add_argument("--policies-dir", default="data/policies", help="Path to policies directory")
    parser.add_argument("--sample-audit", action="store_true", default=True, help="Print sample Chain of Thought audit report")
    args = parser.parse_args()

    print("=================================================================")
    print("      PRICING HUB: AUTOMATED ALLOWABLE AMOUNT VERIFICATION       ")
    print("=================================================================\n")
    print(f"[*] Loading test claims from: {args.claims_file}")

    runner = ValidationRunner(
        contracts_dir=args.contracts_dir,
        policies_dir=args.policies_dir,
    )

    results = runner.run_validation(args.claims_file)

    print("\n-----------------------------------------------------------------")
    print("                  BATCH VERIFICATION RESULTS                     ")
    print("-----------------------------------------------------------------")
    print(f"Total Claims Evaluated : {results['total_claims']}")
    print(f"Claims Passed (Parity) : {results['passed_claims']}")
    print(f"Claims Failed          : {results['failed_claims']}")
    print(f"Concordance Accuracy   : {results['concordance_rate']}%")
    print(f"Total Billed Charges   : ${results['total_billed']:,.2f}")
    print(f"Total Allowable Amount : ${results['total_allowable']:,.2f}")
    print(f"Contractual Discount   : ${results['total_billed'] - results['total_allowable']:,.2f}")
    print(f"Execution Duration     : {results['elapsed_seconds']} seconds")
    if results['elapsed_seconds'] > 0:
        throughput = round(results['total_claims'] / results['elapsed_seconds'], 1)
        print(f"Processing Throughput  : {throughput} claims/second")

    if results["discrepancies"]:
        print(f"\n[!] Discrepancies Detected: {len(results['discrepancies'])}")
        for idx, d in enumerate(results["discrepancies"], 1):
            print(f"    {idx}. Claim {d['claim_id']} Line {d['line_number']} [{d['discrepancy_type']}]: {d['root_cause']}")
    else:
        print("\n[+] SUCCESS: ZERO DISCREPANCIES DETECTED. 100% GROUND TRUTH PARITY ACHIEVED.")

    # Print a sample Chain-of-Thought audit report
    if args.sample_audit:
        print("\n=================================================================")
        print("          SAMPLE AUDIT TRAIL (CHAIN OF THOUGHT CITATION)         ")
        print("=================================================================\n")
        with open(args.claims_file, "r") as f:
            sample_claims = json.load(f)

        # Pick claim 6 (MPPR multi-surgery with Mod 25)
        sample_raw = sample_claims[5] if len(sample_claims) > 5 else sample_claims[0]
        claim, _ = runner.claim_loader.load_claim_from_dict(sample_raw)
        contract = runner.contract_parser.get_contract_for_provider(claim.billing_provider_npi, lob=claim.line_of_business)
        policies = list(runner.policy_parser.policies.values())
        priced = runner.router.price_claim(claim, contract, policies)

        audit_gen = AuditLogGenerator()
        doc = audit_gen.generate_claim_audit_trail(claim, priced)
        print(audit_gen.format_markdown_report(doc))

    print("\n=================================================================")
    print("VERIFICATION COMPLETED.")
    print("=================================================================")


if __name__ == "__main__":
    main()
