"""Script to generate synthetic test data package and the 100-Claim Golden Dataset.
Produces:
1. data/contracts/ (Commercial, Medicare Advantage, Medicaid MCO)
2. data/policies/ (CMS LCD/NCD, Commercial Payer Reimbursement Policies)
3. data/benefits/ (Member SBC & Accumulator Profiles)
4. data/mapping_matrix/ (Rule-to-Policy cross-reference matrix in CSV and JSON)
5. data/claim_line_dispositions/ (Dispositions: Paid, Denied, Suspended)
6. data/integration_tests/ (Cog interaction test cases)
7. data/golden_dataset/ (100 Golden Claims with exact ground truth)
"""

import json
import csv
import os
from typing import Dict, Any, List


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")


def create_contracts():
    contracts_dir = os.path.join(DATA_DIR, "contracts")
    os.makedirs(contracts_dir, exist_ok=True)

    # 1. Commercial Contract
    commercial_contract = {
        "contract_id": "CTR-COMM-2026",
        "contract_name": "Regional Commercial Health Network Agreement",
        "line_of_business": "COMMERCIAL",
        "provider_npi_list": ["1982730192", "1548291034", "1827391029", "1293840192", "1992830111"],
        "effective_start": "2026-01-01",
        "effective_end": "2026-12-31",
        "fee_schedule": {
            "99203": 150.00,
            "99204": 210.00,
            "99213": 120.00,
            "99214": 165.00,
            "99215": 225.00,
            "29881": 1250.00,  # Arthroscopy knee meniscectomy
            "29882": 1400.00,  # Arthroscopy knee meniscus repair
            "45378": 850.00,   # Diagnostic Colonoscopy
            "45380": 950.00,   # Colonoscopy with biopsy
            "71046": 85.00,    # Chest X-ray 2 views
            "71046-26": 35.00, # Professional component
            "71046-TC": 50.00, # Technical component
            "93000": 60.00,    # Electrocardiogram complete
            "93000-26": 25.00, # ECG Professional component
            "93000-TC": 35.00, # ECG Technical component
            "99000": 0.00,     # Specimen handling (Bundled)
            "36415": 15.00,    # Routine venipuncture
        },
        "drg_rules": {
            "470": {
                "drg_code": "470",
                "description": "Major Hip and Knee Joint Replacement w/o MCC",
                "base_rate": 10500.00,
                "relative_weight": 1.95,
                "outlier_threshold": 45000.00,
                "outlier_marginal_rate": 0.80,
            },
            "871": {
                "drg_code": "871",
                "description": "Septicemia or Severe Sepsis w/o MV >96 Hours w/ MCC",
                "base_rate": 10500.00,
                "relative_weight": 1.72,
                "outlier_threshold": 45000.00,
                "outlier_marginal_rate": 0.80,
            },
            "194": {
                "drg_code": "194",
                "description": "Simple Pneumonia & Pleurisy w/ CC",
                "base_rate": 10500.00,
                "relative_weight": 0.98,
                "outlier_threshold": 45000.00,
                "outlier_marginal_rate": 0.80,
            },
        },
        "percent_of_charges_rules": [
            {
                "category": "Unlisted Surgical / Medical Supplies",
                "revenue_code_prefix": "0270",
                "percent_allowable": 0.60,
            },
            {
                "category": "Operating Room Services",
                "revenue_code_prefix": "0360",
                "percent_allowable": 0.65,
            },
        ],
        "per_diem_rates": {
            "0110": 1800.00,  # Room & Board - General
            "0200": 3500.00,  # Intensive Care Unit (ICU)
        },
        "contract_clauses": {
            "Section 3.1": "Professional Fee Schedule: Rates established in Exhibit A govern standard allowable payments.",
            "Section 4.2": "Inpatient Facility DRG Adjudication: Base rate multiplied by CMS Relative Weight. High cost outliers qualify if total billed exceeds $45,000 threshold, paid at 80% marginal factor.",
            "Section 5.1": "Multiple Procedure Payment Reduction (MPPR): Primary surgical procedure reimbursed at 100% of fee schedule; secondary and subsequent qualifying surgical procedures reimbursed at 50%.",
            "Section 6.4": "Diagnostic Splitting: When billed with modifier 26 or TC, allowable splits strictly to professional/technical schedules.",
            "Section 7.3": "Timely Filing Limit: All claims must be submitted within 90 days of the date of service. Untimely claims are non-reimbursable.",
            "Section 8.2": "Incidental and Bundled Codes: CPT 99000 (handling) is considered bundled into primary service and is non-payable.",
        },
    }

    # 2. Medicare Advantage Contract
    medicare_contract = {
        "contract_id": "CTR-MED-ADV-2026",
        "contract_name": "National Medicare Advantage Provider Contract",
        "line_of_business": "MEDICARE",
        "provider_npi_list": ["1649201948", "1748291034", "1982730192"],
        "effective_start": "2026-01-01",
        "effective_end": "2026-12-31",
        "fee_schedule": {
            "99203": 115.00,
            "99204": 168.00,
            "99213": 95.00,
            "99214": 135.00,
            "99215": 185.00,
            "29881": 950.00,
            "29882": 1050.00,
            "45378": 650.00,
            "45380": 730.00,
            "71046": 65.00,
            "71046-26": 28.00,
            "71046-TC": 37.00,
            "93000": 45.00,
            "93000-26": 18.00,
            "93000-TC": 27.00,
            "99000": 0.00,
            "36415": 10.00,
        },
        "drg_rules": {
            "470": {
                "drg_code": "470",
                "description": "Major Hip and Knee Joint Replacement w/o MCC",
                "base_rate": 7200.00,
                "relative_weight": 1.95,
                "outlier_threshold": 40000.00,
                "outlier_marginal_rate": 0.80,
            },
            "871": {
                "drg_code": "871",
                "description": "Septicemia or Severe Sepsis w/o MV >96 Hours w/ MCC",
                "base_rate": 7200.00,
                "relative_weight": 1.72,
                "outlier_threshold": 40000.00,
                "outlier_marginal_rate": 0.80,
            },
            "194": {
                "drg_code": "194",
                "description": "Simple Pneumonia & Pleurisy w/ CC",
                "base_rate": 7200.00,
                "relative_weight": 0.98,
                "outlier_threshold": 40000.00,
                "outlier_marginal_rate": 0.80,
            },
        },
        "percent_of_charges_rules": [
            {
                "category": "Unlisted Hospital Charges",
                "revenue_code_prefix": "0270",
                "percent_allowable": 0.50,
            }
        ],
        "per_diem_rates": {
            "0110": 1350.00,
            "0200": 2600.00,
        },
        "contract_clauses": {
            "Section 2.1": "CMS Fee Schedule Parity: Physician allowable is pegged directly to the CMS MPFS Medicare Advantage rate file.",
            "Section 3.5": "CMS IPPS DRG Methodology: Inpatient stays reimbursed under CMS Inpatient Prospective Payment System base rates.",
            "Section 4.1": "CMS MPPR Regulations: Multiple surgical reductions follow CMS Chapter 13 MPFS rules (50% reduction on secondary).",
            "Section 6.1": "Timely Filing: Medicare Advantage timely filing limit is 365 calendar days from service date.",
        },
    }

    # 3. Medicaid Contract
    medicaid_contract = {
        "contract_id": "CTR-MCD-MCO-2026",
        "contract_name": "Community Medicaid Managed Care Agreement",
        "line_of_business": "MEDICAID",
        "provider_npi_list": ["1382910492", "1982730192", "1182739401"],
        "effective_start": "2026-01-01",
        "effective_end": "2026-12-31",
        "fee_schedule": {
            "99203": 90.00,
            "99204": 130.00,
            "99213": 75.00,
            "99214": 105.00,
            "99215": 145.00,
            "29881": 780.00,
            "29882": 880.00,
            "45378": 520.00,
            "45380": 590.00,
            "71046": 50.00,
            "71046-26": 20.00,
            "71046-TC": 30.00,
            "93000": 35.00,
            "93000-26": 15.00,
            "93000-TC": 20.00,
            "99000": 0.00,
            "36415": 8.00,
        },
        "drg_rules": {
            "470": {
                "drg_code": "470",
                "description": "Major Hip and Knee Joint Replacement w/o MCC",
                "base_rate": 6100.00,
                "relative_weight": 1.95,
                "outlier_threshold": 35000.00,
                "outlier_marginal_rate": 0.75,
            },
            "871": {
                "drg_code": "871",
                "description": "Septicemia or Severe Sepsis w/o MV >96 Hours w/ MCC",
                "base_rate": 6100.00,
                "relative_weight": 1.72,
                "outlier_threshold": 35000.00,
                "outlier_marginal_rate": 0.75,
            },
            "194": {
                "drg_code": "194",
                "description": "Simple Pneumonia & Pleurisy w/ CC",
                "base_rate": 6100.00,
                "relative_weight": 0.98,
                "outlier_threshold": 35000.00,
                "outlier_marginal_rate": 0.75,
            },
        },
        "percent_of_charges_rules": [
            {
                "category": "Medicaid Supplies",
                "revenue_code_prefix": "0270",
                "percent_allowable": 0.45,
            }
        ],
        "per_diem_rates": {
            "0110": 1100.00,
            "0200": 2100.00,
        },
        "contract_clauses": {
            "Section 1.4": "State Medicaid Fee Base: Reimbursed in accordance with the State Department of Health Fee Schedule.",
            "Section 2.3": "Prior Authorization Required: Select surgical procedures require documented state prior authorization.",
            "Section 3.2": "Timely Filing: Medicaid claims must be filed within 180 calendar days of service.",
        },
    }

    with open(os.path.join(contracts_dir, "commercial_provider_contract.json"), "w") as f:
        json.dump(commercial_contract, f, indent=2)
    with open(os.path.join(contracts_dir, "medicare_advantage_contract.json"), "w") as f:
        json.dump(medicare_contract, f, indent=2)
    with open(os.path.join(contracts_dir, "medicaid_managed_care_contract.json"), "w") as f:
        json.dump(medicaid_contract, f, indent=2)
    print("Contracts generated.")


def create_policies():
    policies_dir = os.path.join(DATA_DIR, "policies")
    os.makedirs(policies_dir, exist_ok=True)

    cms_policies = [
        {
            "policy_id": "CMS-NCD-220.4",
            "policy_title": "Diagnostic Ultrasound in Cardiac Procedures",
            "policy_type": "CMS_NCD",
            "paragraph_id": "Paragraph 3.1(a)",
            "target_procedure_codes": ["93000", "93000-26", "93000-TC"],
            "rule_action": "ALLOW",
            "required_diagnosis_codes": ["I25.10", "I50.9", "R07.9", "I10"],
            "bundled_exclusive_codes": [],
            "required_modifiers": [],
            "citation_text": "CMS National Coverage Determination (NCD) 220.4, Paragraph 3.1(a): Diagnostic cardiac evaluation is covered when primary indication includes atherosclerotic heart disease (I25.10), heart failure (I50.9), or chest pain (R07.9).",
            "rule_description": "Medical necessity verification for diagnostic electrocardiograms and cardiac ultrasound.",
            "denial_carc": "CO-16",
        },
        {
            "policy_id": "CMS-LCD-L33587",
            "policy_title": "Spinal Injections and Pain Interventions",
            "policy_type": "CMS_LCD",
            "paragraph_id": "Paragraph 4.2(b)",
            "target_procedure_codes": ["64490", "64493"],
            "rule_action": "ALLOW",
            "required_diagnosis_codes": ["M54.5", "M47.816"],
            "bundled_exclusive_codes": [],
            "required_modifiers": [],
            "citation_text": "CMS Local Coverage Determination (LCD) L33587, Paragraph 4.2(b): Interventional spine injections require documented failed conservative therapy and qualifying lumbar radiculopathy diagnosis.",
            "rule_description": "Facet injection medical necessity and prior authorization guidelines.",
            "denial_carc": "CO-16",
        },
    ]

    commercial_policies = [
        {
            "policy_id": "PAYER-RP-042",
            "policy_title": "Multiple Procedure Payment Reduction (MPPR) for Surgery",
            "policy_type": "COMMERCIAL_REIMBURSEMENT",
            "paragraph_id": "Paragraph 4.1",
            "target_procedure_codes": ["29882", "29881"],
            "rule_action": "REDUCE_50",
            "required_diagnosis_codes": [],
            "bundled_exclusive_codes": [],
            "required_modifiers": ["51", "59"],
            "citation_text": "Commercial Reimbursement Policy RP-042, Paragraph 4.1: When multiple surgical procedures are performed during the same operative session, the highest-valued procedure is reimbursed at 100% and secondary procedures are reduced by 50%.",
            "rule_description": "Applies 50% discount to lower-ranked surgical claim lines when performed in conjunction with primary arthroscopy.",
            "denial_carc": None,
        },
        {
            "policy_id": "PAYER-RP-109",
            "policy_title": "Same-Day Evaluation & Management with Procedure (Modifier -25)",
            "policy_type": "COMMERCIAL_REIMBURSEMENT",
            "paragraph_id": "Paragraph 3.2",
            "target_procedure_codes": ["99213", "99214", "99215"],
            "rule_action": "ALLOW",
            "required_diagnosis_codes": [],
            "bundled_exclusive_codes": [],
            "required_modifiers": ["25"],
            "citation_text": "Commercial Reimbursement Policy RP-109, Paragraph 3.2: E&M codes billed on the same day as a minor surgical procedure are payable only when appended with Modifier -25 indicating a significant, separately identifiable service.",
            "rule_description": "Modifier -25 verification for same-day office visit with procedure.",
            "denial_carc": "CO-16",
        },
        {
            "policy_id": "PAYER-RP-018",
            "policy_title": "Incidental and Bundled Services Policy",
            "policy_type": "COMMERCIAL_REIMBURSEMENT",
            "paragraph_id": "Paragraph 5.1",
            "target_procedure_codes": ["99000"],
            "rule_action": "DENY",
            "required_diagnosis_codes": [],
            "bundled_exclusive_codes": ["36415", "99213", "99214"],
            "required_modifiers": [],
            "citation_text": "Commercial Reimbursement Policy RP-018, Paragraph 5.1: CPT 99000 (specimen handling) is an integral component of venipuncture and office encounters. It is bundled and non-reimbursable.",
            "rule_description": "Automated denial of bundled specimen handling fees under CARC CO-97.",
            "denial_carc": "CO-97",
        },
        {
            "policy_id": "PAYER-RP-003",
            "policy_title": "Timely Filing Limit Adjudication Policy",
            "policy_type": "COMMERCIAL_REIMBURSEMENT",
            "paragraph_id": "Paragraph 1.2",
            "target_procedure_codes": [],
            "rule_action": "DENY",
            "required_diagnosis_codes": [],
            "bundled_exclusive_codes": [],
            "required_modifiers": [],
            "timely_filing_limit_days": 90,
            "citation_text": "Commercial Reimbursement Policy RP-003, Paragraph 1.2: Claims submitted past the 90-day contractual timely filing window are denied with CARC CO-29.",
            "rule_description": "Enforces 90-day submission deadline from the date of service.",
            "denial_carc": "CO-29",
        },
    ]

    with open(os.path.join(policies_dir, "cms_lcd_ncd_policies.json"), "w") as f:
        json.dump(cms_policies, f, indent=2)
    with open(os.path.join(policies_dir, "commercial_reimbursement_policies.json"), "w") as f:
        json.dump(commercial_policies, f, indent=2)
    print("Policies generated.")


def create_benefits():
    benefits_dir = os.path.join(DATA_DIR, "benefits")
    os.makedirs(benefits_dir, exist_ok=True)

    member_benefits = {
        "MEM-COMM-001": {
            "member_id": "MEM-COMM-001",
            "line_of_business": "COMMERCIAL",
            "plan_name": "Premier Silver PPO 2000",
            "individual_deductible": 2000.00,
            "deductible_met": 1500.00,
            "copay_pcp": 25.00,
            "copay_specialist": 50.00,
            "coinsurance_percentage": 0.20,
            "out_of_pocket_max": 7500.00,
            "oop_accumulated": 2100.00,
            "active": True,
        },
        "MEM-MED-042": {
            "member_id": "MEM-MED-042",
            "line_of_business": "MEDICARE",
            "plan_name": "National Medicare Choice Plus",
            "individual_deductible": 0.00,
            "deductible_met": 0.00,
            "copay_pcp": 0.00,
            "copay_specialist": 35.00,
            "coinsurance_percentage": 0.00,
            "out_of_pocket_max": 3400.00,
            "oop_accumulated": 450.00,
            "active": True,
        },
        "MEM-MCD-089": {
            "member_id": "MEM-MCD-089",
            "line_of_business": "MEDICAID",
            "plan_name": "Community State Health Plan",
            "individual_deductible": 0.00,
            "deductible_met": 0.00,
            "copay_pcp": 0.00,
            "copay_specialist": 0.00,
            "coinsurance_percentage": 0.00,
            "out_of_pocket_max": 0.00,
            "oop_accumulated": 0.00,
            "active": True,
        },
    }

    with open(os.path.join(benefits_dir, "member_benefits_accumulators.json"), "w") as f:
        json.dump(member_benefits, f, indent=2)
    print("Benefits generated.")


def create_mapping_matrix():
    matrix_dir = os.path.join(DATA_DIR, "mapping_matrix")
    os.makedirs(matrix_dir, exist_ok=True)

    rows = [
        {
            "rule_id": "RULE-FS-001",
            "rule_name": "Standard Fee Schedule Allowable",
            "line_item_edit": "Allowable pegged to contracted physician fee schedule",
            "contract_section": "Section 3.1 - Standard Fee Schedule",
            "policy_document": "PAYER-RP-001 / CMS MPFS",
            "policy_paragraph": "Paragraph 1.1",
            "adjudication_action": "ALLOW",
            "carc_code": "CO-45",
            "description": "Calculates contractual discount between billed charge and fee schedule allowable."
        },
        {
            "rule_id": "RULE-MPPR-002",
            "rule_name": "Multiple Procedure Payment Reduction (MPPR)",
            "line_item_edit": "Secondary surgical procedure allowable reduced by 50%",
            "contract_section": "Section 5.1 - Multiple Procedure Reductions",
            "policy_document": "PAYER-RP-042",
            "policy_paragraph": "Paragraph 4.1",
            "adjudication_action": "REDUCE_50",
            "carc_code": "CO-59",
            "description": "Reduces second and subsequent surgical procedures performed on same date."
        },
        {
            "rule_id": "RULE-SPLIT-003",
            "rule_name": "Diagnostic Split Modifier 26/TC",
            "line_item_edit": "Splits global diagnostic code into Professional (-26) or Technical (-TC)",
            "contract_section": "Section 6.4 - Diagnostic Splitting",
            "policy_document": "PAYER-RP-055",
            "policy_paragraph": "Paragraph 2.4",
            "adjudication_action": "ALLOW_SPLIT",
            "carc_code": "CO-45",
            "description": "Applies dedicated component fee schedule when modifier 26 or TC is present."
        },
        {
            "rule_id": "RULE-MOD25-004",
            "rule_name": "Modifier -25 Same Day E&M with Procedure",
            "line_item_edit": "Requires Modifier -25 when E&M billed on same date as minor surgery",
            "contract_section": "Section 3.1 & Exhibit C",
            "policy_document": "PAYER-RP-109",
            "policy_paragraph": "Paragraph 3.2",
            "adjudication_action": "ALLOW_OR_DENY",
            "carc_code": "CO-16",
            "description": "Denies E&M without modifier -25 when concurrent surgical code exists."
        },
        {
            "rule_id": "RULE-BUNDLE-005",
            "rule_name": "Incidental Specimen Handling Bundling",
            "line_item_edit": "CPT 99000 bundled into primary lab / office visit",
            "contract_section": "Section 8.2 - Incidental Codes",
            "policy_document": "PAYER-RP-018",
            "policy_paragraph": "Paragraph 5.1",
            "adjudication_action": "DENY",
            "carc_code": "CO-97",
            "description": "Denies handling charge as bundled into primary venipuncture or office code."
        },
        {
            "rule_id": "RULE-DRG-006",
            "rule_name": "Inpatient DRG Case Rate Adjudication",
            "line_item_edit": "Priced via Base Rate x Relative Weight + High-Cost Outlier",
            "contract_section": "Section 4.2 - Inpatient Case Rates",
            "policy_document": "CMS IPPS Final Rule",
            "policy_paragraph": "Section IV.B",
            "adjudication_action": "ALLOW_DRG",
            "carc_code": "CO-45",
            "description": "Calculates prospective DRG payment and checks $45,000 threshold for 80% marginal outlier."
        },
        {
            "rule_id": "RULE-TIMELY-007",
            "rule_name": "Contractual Timely Filing Enforcement",
            "line_item_edit": "Claim filing date > 90 days after service date",
            "contract_section": "Section 7.3 - Timely Filing Limit",
            "policy_document": "PAYER-RP-003",
            "policy_paragraph": "Paragraph 1.2",
            "adjudication_action": "DENY",
            "carc_code": "CO-29",
            "description": "Denies entire claim or line item when submission exceeds contractual filing window."
        },
        {
            "rule_id": "RULE-MED-NEC-008",
            "rule_name": "Medical Necessity LCD/NCD Verification",
            "line_item_edit": "Diagnosis code must match approved CMS LCD indication",
            "contract_section": "Section 2.1 - Clinical Policy Guidelines",
            "policy_document": "CMS-NCD-220.4",
            "policy_paragraph": "Paragraph 3.1(a)",
            "adjudication_action": "ALLOW_OR_DENY",
            "carc_code": "CO-16",
            "description": "Denies diagnostic imaging or specialty procedures when diagnosis fails LCD/NCD criteria."
        },
    ]

    csv_path = os.path.join(matrix_dir, "rule_to_policy_matrix.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = os.path.join(matrix_dir, "rule_to_policy_matrix.json")
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)
    print("Mapping matrix generated.")


def create_claim_dispositions():
    disp_dir = os.path.join(DATA_DIR, "claim_line_dispositions")
    os.makedirs(disp_dir, exist_ok=True)

    dispositions = [
        {
            "case_id": "DISP-CASE-001",
            "category": "PAID",
            "description": "Clean office visit (99214) with valid diagnosis and active contract rate",
            "claim_type": "PROFESSIONAL",
            "expected_disposition": "PAID",
            "expected_carc": "CO-45",
            "notes": "Payment matches fee schedule ($165.00), contractual discount applied.",
        },
        {
            "case_id": "DISP-CASE-002",
            "category": "DENIED",
            "description": "Specimen handling fee (99000) billed alongside venipuncture (36415)",
            "claim_type": "PROFESSIONAL",
            "expected_disposition": "DENIED",
            "expected_carc": "CO-97",
            "notes": "Bundled service; no separate allowable.",
        },
        {
            "case_id": "DISP-CASE-003",
            "category": "DENIED",
            "description": "Claim submitted 120 days post-service exceeding 90-day timely filing limit",
            "claim_type": "PROFESSIONAL",
            "expected_disposition": "DENIED",
            "expected_carc": "CO-29",
            "notes": "Denial for untimely filing.",
        },
        {
            "case_id": "DISP-CASE-004",
            "category": "DENIED",
            "description": "Cardiac diagnostic (93000) billed with non-qualifying diagnosis (Z00.00)",
            "claim_type": "PROFESSIONAL",
            "expected_disposition": "DENIED",
            "expected_carc": "CO-16",
            "notes": "Medical necessity requirement not met under CMS-NCD-220.4.",
        },
        {
            "case_id": "DISP-CASE-005",
            "category": "SUSPENDED",
            "description": "Inpatient high-dollar complex facility claim exceeding $100,000 threshold",
            "claim_type": "FACILITY",
            "expected_disposition": "SUSPENDED",
            "expected_carc": None,
            "notes": "Suspended for manual clinician itemized bill audit.",
        },
    ]

    with open(os.path.join(disp_dir, "disposition_test_cases.json"), "w") as f:
        json.dump(dispositions, f, indent=2)
    print("Claim line dispositions generated.")


def create_integration_tests():
    integ_dir = os.path.join(DATA_DIR, "integration_tests")
    os.makedirs(integ_dir, exist_ok=True)

    cog_fixtures = [
        {
            "test_id": "COG-TEST-001",
            "description": "End-to-End Cog Handshake: Commercial Member with Knee Arthroscopy",
            "member_pick_cog": {
                "input_member_id": "MEM-COMM-001",
                "expected_lob": "COMMERCIAL",
                "expected_plan": "Premier Silver PPO 2000",
                "eligibility_status": "ACTIVE",
            },
            "benefit_cog": {
                "deductible_remaining": 500.00,
                "coinsurance_rate": 0.20,
                "in_network_tier": "TIER_1",
            },
            "contract_cog": {
                "billing_npi": "1982730192",
                "resolved_contract_id": "CTR-COMM-2026",
                "pricing_methodology": "FEE_SCHEDULE",
            },
            "pricing_cog": {
                "procedure_code": "29881",
                "billed_amount": 3500.00,
                "expected_allowable": 1250.00,
            },
            "verification_cog": {
                "expected_allowable": 1250.00,
                "expected_disposition": "PAID",
                "rule_citation": "Section 3.1 / Exhibit A",
            },
        },
        {
            "test_id": "COG-TEST-002",
            "description": "End-to-End Cog Handshake: Medicare Advantage Inpatient Admission",
            "member_pick_cog": {
                "input_member_id": "MEM-MED-042",
                "expected_lob": "MEDICARE",
                "expected_plan": "National Medicare Choice Plus",
                "eligibility_status": "ACTIVE",
            },
            "benefit_cog": {
                "deductible_remaining": 0.00,
                "copay_amount": 0.00,
                "in_network_tier": "TIER_1",
            },
            "contract_cog": {
                "billing_npi": "1649201948",
                "resolved_contract_id": "CTR-MED-ADV-2026",
                "pricing_methodology": "DRG_CASE_RATE",
            },
            "pricing_cog": {
                "drg_code": "470",
                "billed_amount": 25000.00,
                "expected_allowable": 14040.00,  # 7200 * 1.95
            },
            "verification_cog": {
                "expected_allowable": 14040.00,
                "expected_disposition": "PAID",
                "rule_citation": "Section 3.5 / CMS IPPS",
            },
        },
    ]

    with open(os.path.join(integ_dir, "cog_integration_matrix.json"), "w") as f:
        json.dump(cog_fixtures, f, indent=2)
    print("Integration test fixtures generated.")


def create_golden_dataset():
    golden_dir = os.path.join(DATA_DIR, "golden_dataset")
    os.makedirs(golden_dir, exist_ok=True)

    # 100 Curated Golden Claims:
    # 1-25: Commercial Professional
    # 26-45: Commercial Facility
    # 46-65: Medicare Advantage Professional
    # 66-80: Medicare Advantage Facility
    # 81-90: Medicaid Managed Care Professional
    # 91-100: Medicaid Managed Care Facility

    claims = []

    # --- Commercial Professional (1 to 25) ---
    # Case 1-5: Clean Office visits
    for i in range(1, 6):
        cpt = "99214"
        billed = 250.00
        allowed = 165.00
        claims.append({
            "claim_id": f"CLM-COMM-PROF-{i:03d}",
            "claim_type": "PROFESSIONAL",
            "line_of_business": "COMMERCIAL",
            "member_id": "MEM-COMM-001",
            "billing_provider_npi": "1982730192",
            "rendering_provider_npi": "1982730192",
            "principal_diagnosis": "I10",
            "secondary_diagnoses": ["E11.9"],
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": cpt,
                    "billed_amount": billed,
                    "units": 1.0,
                    "modifiers": [],
                    "service_date": "2026-01-15",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["Section 3.1 - Standard Fee Schedule"],
            "line_expectations": [
                {
                    "line_number": 1,
                    "expected_allowable": allowed,
                    "expected_disposition": "PAID",
                    "pricing_methodology": "FEE_SCHEDULE",
                    "denial_carc": None,
                }
            ],
        })

    # Case 6-10: Office visit + Surgical procedure with MPPR and Modifier -25
    # Line 1: 99214 with mod 25 ($165.00)
    # Line 2: 29881 ($1250.00 - primary surgery 100%)
    # Line 3: 29882 ($1400.00 -> reduced 50% to $700.00)
    # Total allowed: 165 + 1250 + 700 = 2115.00
    for i in range(6, 11):
        billed = 6500.00
        allowed = 2115.00
        claims.append({
            "claim_id": f"CLM-COMM-PROF-{i:03d}",
            "claim_type": "PROFESSIONAL",
            "line_of_business": "COMMERCIAL",
            "member_id": "MEM-COMM-001",
            "billing_provider_npi": "1982730192",
            "rendering_provider_npi": "1982730192",
            "principal_diagnosis": "M23.22",
            "secondary_diagnoses": [],
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "99214",
                    "billed_amount": 350.00,
                    "units": 1.0,
                    "modifiers": ["25"],
                    "service_date": "2026-01-15",
                },
                {
                    "line_number": 2,
                    "procedure_code": "29881",
                    "billed_amount": 3200.00,
                    "units": 1.0,
                    "modifiers": [],
                    "service_date": "2026-01-15",
                },
                {
                    "line_number": 3,
                    "procedure_code": "29882",
                    "billed_amount": 2950.00,
                    "units": 1.0,
                    "modifiers": ["51"],
                    "service_date": "2026-01-15",
                },
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": [
                "PAYER-RP-109, Paragraph 3.2",
                "PAYER-RP-042, Paragraph 4.1",
                "Section 5.1 - Multiple Procedure Reductions",
            ],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": 165.00, "expected_disposition": "PAID", "pricing_methodology": "FEE_SCHEDULE", "denial_carc": None},
                {"line_number": 2, "expected_allowable": 1250.00, "expected_disposition": "PAID", "pricing_methodology": "FEE_SCHEDULE", "denial_carc": None},
                {"line_number": 3, "expected_allowable": 700.00, "expected_disposition": "PAID", "pricing_methodology": "MPPR_SURGICAL", "denial_carc": None},
            ],
        })

    # Case 11-15: Diagnostic Split (Chest X-ray 71046 with mod 26 and TC)
    for i in range(11, 16):
        billed = 180.00
        allowed = 35.00  # 71046-26 professional component
        claims.append({
            "claim_id": f"CLM-COMM-PROF-{i:03d}",
            "claim_type": "PROFESSIONAL",
            "line_of_business": "COMMERCIAL",
            "member_id": "MEM-COMM-001",
            "billing_provider_npi": "1982730192",
            "rendering_provider_npi": "1982730192",
            "principal_diagnosis": "R05.9",
            "secondary_diagnoses": [],
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "71046",
                    "billed_amount": billed,
                    "units": 1.0,
                    "modifiers": ["26"],
                    "service_date": "2026-01-15",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["Section 6.4 - Diagnostic Splitting"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": allowed, "expected_disposition": "PAID", "pricing_methodology": "FEE_SCHEDULE", "denial_carc": None}
            ],
        })

    # Case 16-20: Bundled Specimen Handling Denied (99000 denied under CO-97) + Venipuncture paid ($15.00)
    for i in range(16, 21):
        billed = 55.00
        allowed = 15.00
        claims.append({
            "claim_id": f"CLM-COMM-PROF-{i:03d}",
            "claim_type": "PROFESSIONAL",
            "line_of_business": "COMMERCIAL",
            "member_id": "MEM-COMM-001",
            "billing_provider_npi": "1982730192",
            "rendering_provider_npi": "1982730192",
            "principal_diagnosis": "E11.9",
            "secondary_diagnoses": [],
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "36415",
                    "billed_amount": 25.00,
                    "units": 1.0,
                    "modifiers": [],
                    "service_date": "2026-01-15",
                },
                {
                    "line_number": 2,
                    "procedure_code": "99000",
                    "billed_amount": 30.00,
                    "units": 1.0,
                    "modifiers": [],
                    "service_date": "2026-01-15",
                },
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",  # Overall claim has paid line
            "expected_policy_citations": ["PAYER-RP-018, Paragraph 5.1"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": 15.00, "expected_disposition": "PAID", "pricing_methodology": "FEE_SCHEDULE", "denial_carc": None},
                {"line_number": 2, "expected_allowable": 0.00, "expected_disposition": "DENIED", "pricing_methodology": "BUNDLED_PACKAGE", "denial_carc": "CO-97"},
            ],
        })

    # Case 21-25: Timely Filing Denied (Filing date > 90 days from service date)
    for i in range(21, 26):
        billed = 250.00
        allowed = 0.00
        claims.append({
            "claim_id": f"CLM-COMM-PROF-{i:03d}",
            "claim_type": "PROFESSIONAL",
            "line_of_business": "COMMERCIAL",
            "member_id": "MEM-COMM-001",
            "billing_provider_npi": "1982730192",
            "rendering_provider_npi": "1982730192",
            "principal_diagnosis": "I10",
            "secondary_diagnoses": [],
            "filing_date": "2026-06-01",  # 137 days after Jan 15 -> exceeds 90 days
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "99214",
                    "billed_amount": billed,
                    "units": 1.0,
                    "modifiers": [],
                    "service_date": "2026-01-15",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "DENIED",
            "expected_policy_citations": ["PAYER-RP-003, Paragraph 1.2"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": 0.00, "expected_disposition": "DENIED", "pricing_methodology": "FEE_SCHEDULE", "denial_carc": "CO-29"}
            ],
        })

    # --- Commercial Facility (26 to 45) ---
    # Case 26-35: Inpatient DRG 470 (Joint replacement) base allowable $20,475.00 (10500 * 1.95)
    for i in range(26, 36):
        billed = 35000.00
        allowed = 20475.00
        claims.append({
            "claim_id": f"CLM-COMM-FAC-{i:03d}",
            "claim_type": "FACILITY",
            "line_of_business": "COMMERCIAL",
            "member_id": "MEM-COMM-001",
            "billing_provider_npi": "1548291034",
            "rendering_provider_npi": "1548291034",
            "facility_type_code": "111",
            "principal_diagnosis": "M16.11",
            "secondary_diagnoses": ["I10"],
            "admission_date": "2026-01-10",
            "discharge_date": "2026-01-14",
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "0001",
                    "revenue_code": "0110",
                    "billed_amount": billed,
                    "units": 4.0,
                    "drg_code": "470",
                    "service_date": "2026-01-10",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["Section 4.2 - Inpatient Case Rates"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": allowed, "expected_disposition": "PAID", "pricing_methodology": "DRG_CASE_RATE", "denial_carc": None}
            ],
        })

    # Case 36-40: Inpatient DRG 470 High-Cost Outlier (Billed $55,000 > $45,000 threshold)
    # Base: 20475.00 + Outlier: (55000 - 45000) * 0.80 = 8000.00 -> Total: 28475.00
    for i in range(36, 41):
        billed = 55000.00
        allowed = 28475.00
        claims.append({
            "claim_id": f"CLM-COMM-FAC-{i:03d}",
            "claim_type": "FACILITY",
            "line_of_business": "COMMERCIAL",
            "member_id": "MEM-COMM-001",
            "billing_provider_npi": "1548291034",
            "rendering_provider_npi": "1548291034",
            "facility_type_code": "111",
            "principal_diagnosis": "M16.11",
            "secondary_diagnoses": ["I10", "E11.9"],
            "admission_date": "2026-01-10",
            "discharge_date": "2026-01-16",
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "0001",
                    "revenue_code": "0110",
                    "billed_amount": billed,
                    "units": 6.0,
                    "drg_code": "470",
                    "service_date": "2026-01-10",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["Section 4.2 - Inpatient Case Rates & Outlier Threshold"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": allowed, "expected_disposition": "PAID", "pricing_methodology": "DRG_CASE_RATE", "denial_carc": None}
            ],
        })

    # Case 41-45: Outpatient Facility Surgery Percent of Charges (Rev Code 0360 @ 65%)
    # Billed $8,000 -> Allowed $5,200.00
    for i in range(41, 46):
        billed = 8000.00
        allowed = 5200.00
        claims.append({
            "claim_id": f"CLM-COMM-FAC-{i:03d}",
            "claim_type": "FACILITY",
            "line_of_business": "COMMERCIAL",
            "member_id": "MEM-COMM-001",
            "billing_provider_npi": "1548291034",
            "rendering_provider_npi": "1548291034",
            "facility_type_code": "131",
            "principal_diagnosis": "K29.00",
            "secondary_diagnoses": [],
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "45378",
                    "revenue_code": "0360",
                    "billed_amount": billed,
                    "units": 1.0,
                    "service_date": "2026-01-15",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["Section 3.2 - Percent of Billed Charges"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": allowed, "expected_disposition": "PAID", "pricing_methodology": "PERCENT_OF_CHARGES", "denial_carc": None}
            ],
        })

    # --- Medicare Advantage Professional (46 to 65) ---
    # Case 46-55: Medicare Clean Office Visits (99214 @ $135.00)
    for i in range(46, 56):
        billed = 220.00
        allowed = 135.00
        claims.append({
            "claim_id": f"CLM-MED-PROF-{i:03d}",
            "claim_type": "PROFESSIONAL",
            "line_of_business": "MEDICARE",
            "member_id": "MEM-MED-042",
            "billing_provider_npi": "1649201948",
            "rendering_provider_npi": "1649201948",
            "principal_diagnosis": "I10",
            "secondary_diagnoses": ["I25.10"],
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "99214",
                    "billed_amount": billed,
                    "units": 1.0,
                    "modifiers": [],
                    "service_date": "2026-01-15",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["Section 2.1 - CMS Fee Schedule Parity"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": allowed, "expected_disposition": "PAID", "pricing_methodology": "FEE_SCHEDULE", "denial_carc": None}
            ],
        })

    # Case 56-60: Medicare Diagnostic ECG with Medical Necessity indication (93000 @ $45.00)
    for i in range(56, 61):
        billed = 90.00
        allowed = 45.00
        claims.append({
            "claim_id": f"CLM-MED-PROF-{i:03d}",
            "claim_type": "PROFESSIONAL",
            "line_of_business": "MEDICARE",
            "member_id": "MEM-MED-042",
            "billing_provider_npi": "1649201948",
            "rendering_provider_npi": "1649201948",
            "principal_diagnosis": "I25.10",  # Matches CMS-NCD-220.4
            "secondary_diagnoses": [],
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "93000",
                    "billed_amount": billed,
                    "units": 1.0,
                    "modifiers": [],
                    "service_date": "2026-01-15",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["CMS-NCD-220.4, Paragraph 3.1(a)"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": allowed, "expected_disposition": "PAID", "pricing_methodology": "FEE_SCHEDULE", "denial_carc": None}
            ],
        })

    # Case 61-65: Medicare Diagnostic ECG without qualifying diagnosis -> Medical necessity denial (CO-16)
    for i in range(61, 66):
        billed = 90.00
        allowed = 0.00
        claims.append({
            "claim_id": f"CLM-MED-PROF-{i:03d}",
            "claim_type": "PROFESSIONAL",
            "line_of_business": "MEDICARE",
            "member_id": "MEM-MED-042",
            "billing_provider_npi": "1649201948",
            "rendering_provider_npi": "1649201948",
            "principal_diagnosis": "M54.5",  # Low back pain, non-cardiac -> Fails CMS-NCD-220.4
            "secondary_diagnoses": [],
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "93000",
                    "billed_amount": billed,
                    "units": 1.0,
                    "modifiers": [],
                    "service_date": "2026-01-15",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "DENIED",
            "expected_policy_citations": ["CMS-NCD-220.4, Paragraph 3.1(a)"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": 0.00, "expected_disposition": "DENIED", "pricing_methodology": "FEE_SCHEDULE", "denial_carc": "CO-16"}
            ],
        })

    # --- Medicare Advantage Facility (66 to 80) ---
    # Case 66-75: Inpatient DRG 470 Medicare Base: 7200 * 1.95 = $14,040.00
    for i in range(66, 76):
        billed = 28000.00
        allowed = 14040.00
        claims.append({
            "claim_id": f"CLM-MED-FAC-{i:03d}",
            "claim_type": "FACILITY",
            "line_of_business": "MEDICARE",
            "member_id": "MEM-MED-042",
            "billing_provider_npi": "1649201948",
            "rendering_provider_npi": "1649201948",
            "facility_type_code": "111",
            "principal_diagnosis": "M16.11",
            "secondary_diagnoses": ["I10"],
            "admission_date": "2026-01-12",
            "discharge_date": "2026-01-15",
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "0001",
                    "revenue_code": "0110",
                    "billed_amount": billed,
                    "units": 3.0,
                    "drg_code": "470",
                    "service_date": "2026-01-12",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["Section 3.5 - CMS IPPS DRG Methodology"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": allowed, "expected_disposition": "PAID", "pricing_methodology": "DRG_CASE_RATE", "denial_carc": None}
            ],
        })

    # Case 76-80: Inpatient High-Dollar Suspended Claim (> $100,000 threshold for manual audit)
    for i in range(76, 81):
        billed = 115000.00
        allowed = 0.00
        claims.append({
            "claim_id": f"CLM-MED-FAC-{i:03d}",
            "claim_type": "FACILITY",
            "line_of_business": "MEDICARE",
            "member_id": "MEM-MED-042",
            "billing_provider_npi": "1649201948",
            "rendering_provider_npi": "1649201948",
            "facility_type_code": "111",
            "principal_diagnosis": "I21.09",
            "secondary_diagnoses": ["I50.9", "N17.9"],
            "admission_date": "2026-01-02",
            "discharge_date": "2026-01-20",
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "0001",
                    "revenue_code": "0200",
                    "billed_amount": billed,
                    "units": 18.0,
                    "drg_code": "871",
                    "service_date": "2026-01-02",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "SUSPENDED",
            "expected_policy_citations": ["High Dollar Clinical Review Policy (> $100,000 threshold)"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": 0.00, "expected_disposition": "SUSPENDED", "pricing_methodology": "DRG_CASE_RATE", "denial_carc": None}
            ],
        })

    # --- Medicaid Managed Care Professional (81 to 90) ---
    # Case 81-90: Medicaid Office Visits (99214 @ $105.00)
    for i in range(81, 91):
        billed = 160.00
        allowed = 105.00
        claims.append({
            "claim_id": f"CLM-MCD-PROF-{i:03d}",
            "claim_type": "PROFESSIONAL",
            "line_of_business": "MEDICAID",
            "member_id": "MEM-MCD-089",
            "billing_provider_npi": "1382910492",
            "rendering_provider_npi": "1382910492",
            "principal_diagnosis": "J45.909",
            "secondary_diagnoses": [],
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "99214",
                    "billed_amount": billed,
                    "units": 1.0,
                    "modifiers": [],
                    "service_date": "2026-01-15",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["Section 1.4 - State Medicaid Fee Base"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": allowed, "expected_disposition": "PAID", "pricing_methodology": "FEE_SCHEDULE", "denial_carc": None}
            ],
        })

    # --- Medicaid Managed Care Facility (91 to 100) ---
    # Case 91-100: Inpatient DRG 470 Medicaid Base: 6100 * 1.95 = $11,895.00
    for i in range(91, 101):
        billed = 22000.00
        allowed = 11895.00
        claims.append({
            "claim_id": f"CLM-MCD-FAC-{i:03d}",
            "claim_type": "FACILITY",
            "line_of_business": "MEDICAID",
            "member_id": "MEM-MCD-089",
            "billing_provider_npi": "1382910492",
            "rendering_provider_npi": "1382910492",
            "facility_type_code": "111",
            "principal_diagnosis": "M16.11",
            "secondary_diagnoses": [],
            "admission_date": "2026-01-10",
            "discharge_date": "2026-01-13",
            "filing_date": "2026-02-01",
            "total_billed_amount": billed,
            "lines": [
                {
                    "line_number": 1,
                    "procedure_code": "0001",
                    "revenue_code": "0110",
                    "billed_amount": billed,
                    "units": 3.0,
                    "drg_code": "470",
                    "service_date": "2026-01-10",
                }
            ],
            "expected_total_allowable": allowed,
            "expected_disposition": "PAID",
            "expected_policy_citations": ["Section 1.4 - State Medicaid Fee Base & DRG Rates"],
            "line_expectations": [
                {"line_number": 1, "expected_allowable": allowed, "expected_disposition": "PAID", "pricing_methodology": "DRG_CASE_RATE", "denial_carc": None}
            ],
        })

    # Save manifest and claim files
    manifest = {
        "dataset_name": "Pricing Hub 100-Claim Golden Dataset",
        "version": "1.0.0",
        "total_claims": len(claims),
        "breakdown": {
            "commercial_professional": 25,
            "commercial_facility": 20,
            "medicare_professional": 20,
            "medicare_facility": 15,
            "medicaid_professional": 10,
            "medicaid_facility": 10,
        },
        "supported_methodologies": [
            "FEE_SCHEDULE",
            "PERCENT_OF_CHARGES",
            "DRG_CASE_RATE",
            "MPPR_SURGICAL",
            "BUNDLED_PACKAGE",
        ],
        "disposition_counts": {
            "PAID": 85,
            "DENIED": 10,
            "SUSPENDED": 5,
        },
    }

    with open(os.path.join(golden_dir, "golden_dataset_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    prof_claims = [c for c in claims if c["claim_type"] == "PROFESSIONAL"]
    fac_claims = [c for c in claims if c["claim_type"] == "FACILITY"]

    with open(os.path.join(golden_dir, "golden_claims_professional.json"), "w") as f:
        json.dump(prof_claims, f, indent=2)
    with open(os.path.join(golden_dir, "golden_claims_facility.json"), "w") as f:
        json.dump(fac_claims, f, indent=2)
    with open(os.path.join(golden_dir, "golden_claims_all.json"), "w") as f:
        json.dump(claims, f, indent=2)

    print(f"Golden dataset created: {len(claims)} claims generated.")


def main():
    print("Generating synthetic test fixtures and golden dataset...")
    create_contracts()
    create_policies()
    create_benefits()
    create_mapping_matrix()
    create_claim_dispositions()
    create_integration_tests()
    create_golden_dataset()
    print("All fixtures generated successfully!")


if __name__ == "__main__":
    main()
