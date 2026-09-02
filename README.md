# Pricing Hub Agentic Skill (`pricing-hub-skill`)

An autonomous agentic skill designed to resolve the core operational bottlenecks of the Pricing Hub: accelerating contract ingestion, automating allowable amount verification, providing real-time pipeline visibility across **Loaded**, **Outstanding**, and **Stalled** loads, and securing migration SLAs.

![Pricing Hub Skill Architecture and Workflow](assets/pricing_hub_workflow.png)

---

## Key Capabilities

1. **Contract and Policy Ingestion Subsystem**:
   - Ingests provider contracts, rate cards, and CMS / commercial reimbursement policies.
   - Extracts fee schedules, DRG relative weights, % of billed charges, per diem rates, and contractual clauses.
   - Standardizes parameters into normalized data models for the claim pricing engine.

2. **Automated Allowable Amount Verification**:
   - Evaluates Professional (837P) and Facility (837I) claims across **Commercial**, **Medicare**, and **Medicaid** lines of business.
   - Accurately computes allowable amounts using Fee Schedules, DRG Case Rates, % of Charges, MPPR 50% surgical reductions, and modifier splits (-26, -TC).
   - Generates an auditable **Chain of Thought** citing exact contract sections and policy paragraphs.
   - Detects discrepancies (allowable deltas, unexpected denials, disposition mismatches).

3. **Real-Time Pricing Load Tracker & Bottleneck Pinpointer**:
   - Categorizes pricing loads into `LOADED`, `OUTSTANDING`, and `STALLED`.
   - Automatically pinpoints bottleneck root causes (`MISSING_FEE_SCHEDULE`, `PROVIDER_NPI_UNMAPPED`, `RATE_CARD_DATE_OVERLAP`, `VALIDATION_VARIANCE_BREACH`, `DEPENDENCY_TIMEOUT`).
   - Computes dynamic completion ETAs and triggers real-time alerts upon SLA breach risks.

4. **Synthetic Test Data & Validation Documentation Package**:
   - **100-Claim Golden Dataset**: Fully curated across Commercial, Medicare Advantage, and Medicaid for both Professional and Facility claims with known ground truth.
   - **Rule-to-Policy Mapping Matrix**: Cross-references every line-item edit and CARC code to its governing contract clause and policy paragraph.
   - **Claim-Line Disposition Set**: Test cases for `PAID`, `DENIED` (CO-16, CO-97, CO-45, CO-29), and `SUSPENDED` (> $100k review).
   - **Inter-Cog Integration Fixtures**: Simulates end-to-end handshakes across `Member Pick Cog` -> `Benefit Accumulator Cog` -> `Contract Pick Cog` -> `Pricing Engine Cog`.

5. **Strict Scope Enforcement Gate**:
   - Supported: Commercial, Medicare, Medicaid; Professional (837P) and Facility (837I).
   - Excluded: Immediately rejects Dental (837D), Vision, and Pharmacy (NCPDP) with `REJECT_UNSUPPORTED_LOB_EXCLUSION`.

---

## How to Use This Skill: A Non-Technical Guide

This skill serves as an automated pricing analyst and operations coordinator for health insurance claims. In standard healthcare operations, updating provider contracts, verifying payment rules, and tracking system migrations requires significant manual cross-referencing between legal contracts, clinical policies, and fee tables. When a rate or provider identifier is missing, batches stall in queue, delaying provider reimbursements and jeopardizing migration deadlines.

This skill automates these workflows through three core operational functions:

### 1. Ingesting Contracts and Policies Automatically
Rather than requiring analysts to manually transcribe procedure codes and dollar amounts into billing databases, the skill reads contract agreements (PDFs and structured rate cards) and reimbursement policy guidelines directly.

- **What happens**: The system parses the document, verifies that effective date ranges are continuous, checks that no required rates are missing, and indexes every procedure code.
- **Example**: When an operations team receives an updated commercial provider agreement, the file is placed into the contracts directory and the ingestion process is triggered. The skill extracts all office visit and surgical rates, confirms date validity, and loads them into memory for claims pricing.

### 2. Auditing and Verifying Claim Calculations
Before a health plan pays live claims or migrates to a new pricing platform, operations leadership must verify that claims pay the exact contracted amount. The skill adjudicates test claims against ground-truth benchmarks and flags any variance.

- **What happens**: Each service line is priced according to contracted fee schedules, inpatient hospital case rates (DRGs), or percentage-of-charge rules. When multiple surgical procedures take place during the same session, the skill automatically discounts secondary procedures by 50 percent according to standard payment reduction guidelines. An auditable trail is produced citing the governing contract section and policy paragraph.
- **Example**: A physician submits a bill for $3,500 for a knee arthroscopy (CPT code 29881) alongside an office visit (CPT code 99214). The skill verifies that the office visit carries modifier 25 (allowing separate payment at $165.00), applies the contracted fee of $1,250.00 for the surgical procedure, and confirms a zero-dollar discrepancy against expected outcomes.

### 3. Pinpointing Operational Bottlenecks in Real Time
During system migrations or high-volume processing cycles, pricing loads progress through three defined stages:
- **Loaded**: Ingestion and baseline verification are complete; the contract is ready for live adjudication.
- **Outstanding**: The load is actively processing within expected turnaround times.
- **Stalled**: Processing is halted due to a specific bottleneck requiring intervention.

Instead of issuing generic failure messages, the skill identifies the precise root cause and provides actionable next steps:
- **Example**: If a Medicaid contract load is marked as Stalled, the system indicates:
  - Bottleneck Reason: Provider NPIs associated with the contract are not registered in the credentialing registry.
  - Remediation: The provider network team must map the NPI to an active billing entity before processing can resume.
- Operational managers can monitor all active loads, completion percentages, and projected completion dates using either the command line or the browser dashboard.

---

## Directory Structure

```text
pricing-hub-skill/
├── LICENSE                           # Apache License, Version 2.0
├── SKILL.md                          # Main agentic skill instruction runbook
├── README.md                         # System documentation and developer guide
├── assets/                           # Document assets and workflow diagrams
│   └── pricing_hub_workflow.png      # Architectural workflow diagram
├── configs/
│   └── pricing_hub_config.yaml       # LOB boundaries, SLA thresholds, alert settings
├── data/
│   ├── contracts/                    # Commercial, Medicare, and Medicaid rate cards (JSON & PDF)
│   │   ├── commercial_provider_contract.json / .pdf
│   │   ├── medicare_advantage_contract.json / .pdf
│   │   └── medicaid_managed_care_contract.json / .pdf
│   ├── policies/                     # CMS LCD/NCD & commercial reimbursement policies (JSON & PDF)
│   │   ├── CMS_NCD_220_4_Cardiac_Diagnostic_Ultrasound.pdf
│   │   ├── CMS_LCD_L33587_Spinal_Injections_Interventions.pdf
│   │   ├── PAYER_RP_042_Multiple_Procedure_Payment_Reduction.pdf
│   │   ├── PAYER_RP_109_Same_Day_EM_Modifier_25.pdf
│   │   ├── PAYER_RP_018_Incidental_Bundled_Services.pdf
│   │   └── PAYER_RP_003_Timely_Filing_Limit.pdf
│   ├── benefits/                     # Member SBC profiles and accumulators (JSON & PDF)
│   │   ├── member_benefits_accumulators.json
│   │   └── SBC_Commercial_Silver_PPO_2000.pdf / SBC_Medicare... / SBC_Medicaid...
│   ├── claims_x12/                   # Raw X12 EDI files & parsed loop structures
│   │   ├── sample_837p_professional.x12
│   │   ├── sample_837i_facility.x12
│   │   ├── sample_837d_dental_excluded.x12
│   │   └── sample_parsed_x12_loops.json
│   ├── golden_dataset/               # 100-Claim Golden Dataset with ground truth
│   │   ├── golden_dataset_manifest.json
│   │   ├── golden_claims_all.json
│   │   ├── golden_claims_professional.json
│   │   └── golden_claims_facility.json
│   ├── mapping_matrix/               # Rule-to-Policy cross-reference matrix (CSV & JSON)
│   │   ├── rule_to_policy_matrix.csv
│   │   └── rule_to_policy_matrix.json
│   ├── claim_line_dispositions/      # Disposition test cases (Paid, Denied, Suspended)
│   │   └── disposition_test_cases.json
│   └── integration_tests/            # Cog interaction test fixtures (JSON & CSV)
│       ├── cog_integration_matrix.json
│       ├── cog_integration_test_file.csv
│       └── cog_integration_test_file.json
├── src/
│   ├── models/                       # Domain models (Claim, Contract, Policy, Pricing, Monitoring)
│   ├── ingestion/                    # Parsers for contracts (JSON/PDF), policies, and X12 claims
│   ├── pricing_engine/               # Fee schedule, DRG, % of charges, and MPPR calculators
│   ├── verification/                 # Discrepancy detector and Chain-of-Thought audit generator
│   ├── monitoring/                   # Load tracker, bottleneck analyzer, and alert dispatcher
│   ├── cogs/                         # Inter-cog pipeline simulators
│   └── ui/                           # Management and process inspector UI
│       ├── process_inspector.html    # Interactive process inspector with Light/Dark mode
│       └── dashboard.html            # Web-based monitoring and verification UI
├── scripts/
│   ├── run_ingestion.py              # Ingests contracts and policies CLI
│   ├── run_verification.py           # Runs allowable validation on claims CLI
│   ├── monitor_loads.py              # Real-time pipeline monitoring dashboard CLI
│   ├── launch_ui.py                  # Local HTTP server runner for process inspector dashboard
│   ├── generate_fixtures.py          # Synthetic dataset and golden claim generator
│   └── generate_synthetic_pdfs.py    # Generates contract, policy, and SBC PDFs + X12 EDI samples
└── tests/                            # 23-test pytest suite
    ├── test_ingestion.py
    ├── test_pricing_engine.py
    ├── test_verification.py
    ├── test_monitoring.py
    ├── test_golden_dataset.py
    └── test_cog_integration.py
```

---

## Interactive Process Inspector & Dashboard UI

The skill includes an interactive, zero-dependency visual interface designed for direct rendering in iframe environments or standalone web browsers.

### Key Visual Elements and Capabilities:
- **Light and Dark Mode Toggle**: Persistent theme switcher powered by CSS custom properties, allowing users to alternate between clean enterprise light and dark themes.
- **1. Ingestion Inspector**: Search and inspect active fee schedules, DRG hospital weights, and CMS LCD/NCD coverage policies.
- **2. Interactive Adjudicator**: Real-time claims pricing calculator allowing users to test CPT codes, surgical modifier reductions (-51), split diagnostic components (-26 / -TC), bundling edits, and timely filing rules with immediate allowable calculations.
- **3. Verification Parity Explorer**: Interactive browser for the 100-claim Golden Dataset with filtering by line of business, concordance validation, and expandable step-by-step Chain-of-Thought audit logs.
- **4. Load Pipeline and Bottleneck Resolver**: Visualizes load progression across Loaded, Outstanding, and Stalled states, with an interactive "Resolve and Re-Ingest" simulator to demonstrate unblocking stalled pipelines.
- **5. Multi-Cog Flow**: Interactive visualizer tracing payloads across Member, Benefit, Contract, and Pricing engine cogs.

### Accessing the Interface:
- **Direct File Access**: Open `src/ui/process_inspector.html` directly in any web browser.
- **Local HTTP Runner**: Run `python3 scripts/launch_ui.py` to serve the interface locally on port 8080.

---

## Quickstart & CLI Commands

### 1. Ingest Contracts and Policies
```bash
python3 scripts/run_ingestion.py
```

### 2. Run Automated Allowable Verification (100 Golden Claims)
```bash
python3 scripts/run_verification.py
```
*Expected Result: 100/100 claims passed (100.0% concordance), zero discrepancies.*

### 3. Launch Real-Time Pricing Load Monitor
```bash
python3 scripts/monitor_loads.py
```
*Displays pipeline status (`LOADED`, `OUTSTANDING`, `STALLED`), throughput, ETAs, bottleneck diagnostics, and alert dispatches.*

### 4. Run Pytest Test Suite
```bash
pytest -v
```
*23/23 tests passing in < 0.35s.*

---

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for the full license text.

