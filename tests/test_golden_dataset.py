"""Test Suite for 100-Claim Golden Dataset Parity and Verification."""

import pytest
from src.verification.validation_runner import ValidationRunner


def test_100_claim_golden_dataset_parit():
    runner = ValidationRunner(
        contracts_dir="data/contracts",
        policies_dir="data/policies",
        allowable_tolerance=0.01,
    )

    results = runner.run_validation("data/golden_dataset/golden_claims_all.json")

    assert results["total_claims"] == 100
    assert results["passed_claims"] == 100
    assert results["failed_claims"] == 0
    assert results["concordance_rate"] == 100.0
    assert len(results["discrepancies"]) == 0
    assert results["total_allowable"] > 0.0
    assert results["total_billed"] > results["total_allowable"]
