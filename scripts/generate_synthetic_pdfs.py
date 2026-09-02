"""Script to generate synthetic PDF contracts, CMS/Payer policy PDFs, SBC PDFs,
and realistic X12 EDI claims data to provide comprehensive test data for the Pricing Hub Skill.
"""

import os
import json
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")


def generate_contract_pdfs():
    contracts_dir = os.path.join(DATA_DIR, "contracts")
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h2_style = styles["Heading2"]
    h3_style = styles["Heading3"]
    body_style = styles["Normal"]

    # 1. Commercial Provider Contract PDF
    comm_pdf_path = os.path.join(contracts_dir, "commercial_provider_contract.pdf")
    doc = SimpleDocTemplate(comm_pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = [
        Paragraph("MASTER PARTICIPATING PROVIDER SERVICES AGREEMENT", title_style),
        Paragraph("Contract Reference: CTR-COMM-2026", h3_style),
        Spacer(1, 10),
        Paragraph("<b>Plan:</b> Regional Commercial Health Network | <b>Line of Business:</b> Commercial (HMO/PPO)", body_style),
        Paragraph("<b>Effective Dates:</b> January 1, 2026 through December 31, 2026", body_style),
        Paragraph("<b>Participating NPIs:</b> 1982730192, 1548291034, 1827391029, 1293840192, 1992830111", body_style),
        Spacer(1, 15),
        Paragraph("ARTICLE III: REIMBURSEMENT METHODOLOGIES", h2_style),
        Paragraph("<b>Section 3.1 - Professional Fee Schedule:</b> Participating Provider shall be reimbursed for Covered Services rendered to Commercial Members in accordance with the allowable fee schedule rates set forth in Exhibit A attached hereto.", body_style),
        Spacer(1, 8),
        Paragraph("<b>Section 4.2 - Inpatient Facility DRG Adjudication:</b> Inpatient acute care hospital admissions shall be reimbursed under the CMS MS-DRG prospective payment methodology utilizing a hospital-specific base rate of $10,500.00 multiplied by the CMS Relative Weight. Cases where total billed charges exceed the high-cost outlier threshold of $45,000.00 shall qualify for an outlier payment calculated at an eighty percent (80%) marginal rate for charges exceeding the threshold.", body_style),
        Spacer(1, 8),
        Paragraph("<b>Section 5.1 - Multiple Procedure Payment Reduction (MPPR):</b> When multiple qualifying surgical procedures are performed by the same physician during the same operative encounter, the primary procedure with the highest contracted allowable shall be reimbursed at 100%, and the secondary and subsequent procedures shall be reimbursed at 50% of the allowable schedule.", body_style),
        Spacer(1, 8),
        Paragraph("<b>Section 6.4 - Diagnostic Splitting:</b> Diagnostic radiological and cardiovascular procedures billed with Modifier 26 (Professional Component) or Modifier TC (Technical Component) shall be reimbursed strictly in accordance with the component schedules defined in Exhibit A.", body_style),
        Spacer(1, 8),
        Paragraph("<b>Section 7.3 - Timely Filing Limits:</b> Claims must be submitted within ninety (90) calendar days from the date of service. Untimely claims submitted after 90 days are subject to contractual denial under CARC CO-29.", body_style),
        Spacer(1, 8),
        Paragraph("<b>Section 8.2 - Bundled & Incidental Codes:</b> Incidental services including CPT 99000 (specimen handling) are deemed bundled into primary evaluation or venipuncture services and are non-reimbursable (CARC CO-97).", body_style),
        Spacer(1, 15),
        Paragraph("EXHIBIT A: COMMERCIAL FEE SCHEDULE (EXCERPT)", h2_style),
    ]

    table_data = [
        ["CPT/HCPCS", "Description", "Contracted Allowable"],
        ["99213", "Office Visit - Level 3 Established", "$120.00"],
        ["99214", "Office Visit - Level 4 Established", "$165.00"],
        ["99215", "Office Visit - Level 5 Established", "$225.00"],
        ["29881", "Knee Arthroscopy w/ Meniscectomy", "$1,250.00"],
        ["29882", "Knee Arthroscopy w/ Meniscus Repair", "$1,400.00"],
        ["71046", "Chest X-Ray 2 Views (Global)", "$85.00"],
        ["71046-26", "Chest X-Ray (Professional)", "$35.00"],
        ["71046-TC", "Chest X-Ray (Technical)", "$50.00"],
        ["93000", "Electrocardiogram Routine (Global)", "$60.00"],
        ["99000", "Specimen Handling & Transport", "$0.00 (Bundled)"],
    ]
    t = Table(table_data, colWidths=[100, 260, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t)
    doc.build(story)

    # 2. Medicare Advantage Contract PDF
    med_pdf_path = os.path.join(contracts_dir, "medicare_advantage_contract.pdf")
    doc2 = SimpleDocTemplate(med_pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story2 = [
        Paragraph("MEDICARE ADVANTAGE PARTICIPATING PROVIDER AGREEMENT", title_style),
        Paragraph("Contract Reference: CTR-MED-ADV-2026", h3_style),
        Spacer(1, 10),
        Paragraph("<b>Plan:</b> National Medicare Choice Plus | <b>Line of Business:</b> Medicare Advantage", body_style),
        Paragraph("<b>Effective Window:</b> January 1, 2026 to December 31, 2026", body_style),
        Spacer(1, 12),
        Paragraph("SECTION 2.1 - CMS MPFS FEE SCHEDULE PARITY", h2_style),
        Paragraph("Allowable amounts for professional services are established based on the CMS National Physician Fee Schedule (MPFS) with applicable geographic practice cost indices (GPCI).", body_style),
        Spacer(1, 8),
        Paragraph("SECTION 3.5 - CMS IPPS DRG METHODOLOGY", h2_style),
        Paragraph("Inpatient facility admissions are reimbursed under CMS Inpatient Prospective Payment System (IPPS) MS-DRG schedules using a base rate of $7,200.00 and an outlier threshold of $40,000.00.", body_style),
        Spacer(1, 8),
        Paragraph("SECTION 6.1 - TIMELY FILING LIMIT", h2_style),
        Paragraph("Medicare Advantage claims must be filed within 365 calendar days from the date of service in accordance with CMS regulations.", body_style),
    ]
    doc2.build(story2)

    # 3. Medicaid Managed Care Contract PDF
    mcd_pdf_path = os.path.join(contracts_dir, "medicaid_managed_care_contract.pdf")
    doc3 = SimpleDocTemplate(mcd_pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story3 = [
        Paragraph("MEDICAID MANAGED CARE ORGANIZATION (MCO) AGREEMENT", title_style),
        Paragraph("Contract Reference: CTR-MCD-MCO-2026", h3_style),
        Spacer(1, 10),
        Paragraph("<b>Plan:</b> Community Medicaid Managed Care | <b>Line of Business:</b> Medicaid MCO", body_style),
        Spacer(1, 12),
        Paragraph("SECTION 1.4 - STATE MEDICAID FEE BASE", h2_style),
        Paragraph("Reimbursement is established pursuant to the State Department of Health Medicaid Fee Schedule (base rate $6,100.00 for inpatient DRG). Timely filing limit is 180 calendar days.", body_style),
    ]
    doc3.build(story3)
    print("Contract PDFs generated.")


def generate_policy_pdfs():
    policies_dir = os.path.join(DATA_DIR, "policies")
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h2_style = styles["Heading2"]
    body_style = styles["Normal"]

    # 1. CMS NCD 220.4 PDF
    ncd_pdf = os.path.join(policies_dir, "CMS_NCD_220_4_Cardiac_Diagnostic_Ultrasound.pdf")
    doc_ncd = SimpleDocTemplate(ncd_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story_ncd = [
        Paragraph("CENTERS FOR MEDICARE & MEDICAID SERVICES (CMS)", title_style),
        Paragraph("National Coverage Determination (NCD) 220.4: Diagnostic Ultrasound in Cardiac Procedures", h2_style),
        Spacer(1, 12),
        Paragraph("<b>Effective Date:</b> January 1, 2026 | <b>Tracking Code:</b> CMS-NCD-220.4", body_style),
        Paragraph("<b>Target Procedure Codes:</b> 93000, 93000-26, 93000-TC (Electrocardiogram and Cardiac Ultrasound)", body_style),
        Spacer(1, 10),
        Paragraph("<b>Coverage Criteria & Medical Necessity (Paragraph 3.1(a)):</b>", body_style),
        Paragraph("Diagnostic cardiac evaluation is covered when the primary clinical indication demonstrates medical necessity, defined as documented atherosclerotic heart disease (ICD-10 I25.10), heart failure (I50.9), essential hypertension (I10), or acute chest pain (R07.9). Services billed without a qualifying medical necessity diagnosis are denied under CARC CO-16.", body_style),
    ]
    doc_ncd.build(story_ncd)

    # 2. CMS LCD L33587 PDF
    lcd_pdf = os.path.join(policies_dir, "CMS_LCD_L33587_Spinal_Injections_Interventions.pdf")
    doc_lcd = SimpleDocTemplate(lcd_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story_lcd = [
        Paragraph("CENTERS FOR MEDICARE & MEDICAID SERVICES (CMS)", title_style),
        Paragraph("Local Coverage Determination (LCD) L33587: Spinal Injections for Pain Interventions", h2_style),
        Spacer(1, 12),
        Paragraph("<b>Paragraph 4.2(b) - Clinical Documentation Criteria:</b>", body_style),
        Paragraph("Facet joint and interventional spinal injections (CPT 64490, 64493) require prior authorization and documented failed conservative therapy with qualifying diagnosis (M54.5, M47.816). Non-qualifying claims deny with CARC CO-16.", body_style),
    ]
    doc_lcd.build(story_lcd)

    # 3. Commercial Policy RP-042 (MPPR) PDF
    rp042_pdf = os.path.join(policies_dir, "PAYER_RP_042_Multiple_Procedure_Payment_Reduction.pdf")
    doc_rp042 = SimpleDocTemplate(rp042_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story_rp042 = [
        Paragraph("COMMERCIAL REIMBURSEMENT POLICY: PAYER-RP-042", title_style),
        Paragraph("Multiple Procedure Payment Reduction (MPPR) for Surgical Procedures", h2_style),
        Spacer(1, 12),
        Paragraph("<b>Paragraph 4.1 - Methodology and Application:</b>", body_style),
        Paragraph("When multiple surgical procedures are performed during the same operative session by the same provider, the highest-valued procedure is reimbursed at 100% of the contracted fee schedule. The secondary and all subsequent qualifying surgical procedures (e.g. CPT 29882 billed with 29881) are reduced by fifty percent (50%). Modifier 51 or MPPR edits indicate the secondary procedure discount.", body_style),
    ]
    doc_rp042.build(story_rp042)

    # 4. Commercial Policy RP-109 (Modifier -25) PDF
    rp109_pdf = os.path.join(policies_dir, "PAYER_RP_109_Same_Day_EM_Modifier_25.pdf")
    doc_rp109 = SimpleDocTemplate(rp109_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story_rp109 = [
        Paragraph("COMMERCIAL REIMBURSEMENT POLICY: PAYER-RP-109", title_style),
        Paragraph("Same-Day Evaluation & Management with Procedure (Modifier -25)", h2_style),
        Spacer(1, 12),
        Paragraph("<b>Paragraph 3.2 - Documentation Criteria:</b>", body_style),
        Paragraph("Evaluation and Management (E&M) services (CPT 99213, 99214, 99215) billed on the same date of service as a minor surgical procedure are payable only when appended with Modifier -25 indicating a significant, separately identifiable medical service. Claims lacking Modifier -25 are denied with CARC CO-16.", body_style),
    ]
    doc_rp109.build(story_rp109)

    # 5. Commercial Policy RP-018 (Bundled Services) PDF
    rp018_pdf = os.path.join(policies_dir, "PAYER_RP_018_Incidental_Bundled_Services.pdf")
    doc_rp018 = SimpleDocTemplate(rp018_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story_rp018 = [
        Paragraph("COMMERCIAL REIMBURSEMENT POLICY: PAYER-RP-018", title_style),
        Paragraph("Incidental and Bundled Medical Services Policy", h2_style),
        Spacer(1, 12),
        Paragraph("<b>Paragraph 5.1 - Specimen Handling Bundling:</b>", body_style),
        Paragraph("CPT 99000 (specimen handling) is an integral component of routine office visits and venipuncture. It is considered bundled and non-reimbursable. Disallowed line items receive CARC CO-97.", body_style),
    ]
    doc_rp018.build(story_rp018)

    # 6. Commercial Policy RP-003 (Timely Filing) PDF
    rp003_pdf = os.path.join(policies_dir, "PAYER_RP_003_Timely_Filing_Limit.pdf")
    doc_rp003 = SimpleDocTemplate(rp003_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story_rp003 = [
        Paragraph("COMMERCIAL REIMBURSEMENT POLICY: PAYER-RP-003", title_style),
        Paragraph("Contractual Timely Filing Limits", h2_style),
        Spacer(1, 12),
        Paragraph("<b>Paragraph 1.2 - Commercial 90-Day Submission Deadline:</b>", body_style),
        Paragraph("Claims submitted later than 90 calendar days from the date of service are denied as untimely filing under CARC CO-29. Members are held harmless from billed charges.", body_style),
    ]
    doc_rp003.build(story_rp003)
    print("Policy PDFs generated.")


def generate_sbc_pdfs():
    benefits_dir = os.path.join(DATA_DIR, "benefits")
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h2_style = styles["Heading2"]
    body_style = styles["Normal"]

    # 1. Commercial SBC PDF
    comm_sbc_pdf = os.path.join(benefits_dir, "SBC_Commercial_Silver_PPO_2000.pdf")
    doc = SimpleDocTemplate(comm_sbc_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = [
        Paragraph("SUMMARY OF BENEFITS AND COVERAGE (SBC)", title_style),
        Paragraph("Plan: Premier Silver PPO 2000 | Coverage Period: 01/01/2026 - 12/31/2026", h2_style),
        Spacer(1, 10),
        Paragraph("This document provides a summary of cost-sharing responsibilities, deductible accumulators, and coverage limits for Member MEM-COMM-001.", body_style),
        Spacer(1, 12),
    ]

    sbc_table = [
        ["Important Questions", "Answers", "Why This Matters"],
        ["Overall Deductible?", "$2,000 Individual / $4,000 Family", "You must pay this amount before plan begins paying."],
        ["Deductible Met to Date?", "$1,500.00 met ($500.00 remaining)", "Deductible is 75% fulfilled."],
        ["Primary Care Copay?", "$25.00 copay per visit", "Flat copay for in-network PCP."],
        ["Specialist Copay?", "$50.00 copay per visit", "Flat copay for in-network specialists."],
        ["Coinsurance?", "20% in-network / 40% out-of-network", "Plan pays 80% of allowable after deductible."],
        ["Out-of-Pocket Maximum?", "$7,500 Individual", "The most you will pay during the policy year."],
        ["OOP Accumulated?", "$2,100.00 accumulated", "$5,400.00 remaining until 100% plan payment."],
    ]
    t = Table(sbc_table, colWidths=[140, 180, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0D9488")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#99F6E4")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0FDFA")]),
    ]))
    story.append(t)
    doc.build(story)

    # 2. Medicare Advantage SBC PDF
    med_sbc_pdf = os.path.join(benefits_dir, "SBC_Medicare_Advantage_Choice_Plus.pdf")
    doc2 = SimpleDocTemplate(med_sbc_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story2 = [
        Paragraph("SUMMARY OF BENEFITS: MEDICARE ADVANTAGE", title_style),
        Paragraph("Plan: National Medicare Choice Plus | Member: MEM-MED-042", h2_style),
        Spacer(1, 10),
        Paragraph("<b>Deductible:</b> $0.00 | <b>PCP Copay:</b> $0.00 | <b>Specialist Copay:</b> $35.00 | <b>Inpatient Hospital:</b> $295/day (Days 1-5) | <b>OOP Max:</b> $3,400.00", body_style),
    ]
    doc2.build(story2)

    # 3. Medicaid SBC PDF
    mcd_sbc_pdf = os.path.join(benefits_dir, "SBC_Medicaid_Community_Health_Plan.pdf")
    doc3 = SimpleDocTemplate(mcd_sbc_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story3 = [
        Paragraph("MEMBER BENEFIT SUMMARY: MEDICAID MCO", title_style),
        Paragraph("Plan: Community State Health Plan | Member: MEM-MCD-089", h2_style),
        Spacer(1, 10),
        Paragraph("<b>Cost Sharing:</b> $0.00 Copay / $0.00 Deductible for all essential health benefits.", body_style),
    ]
    doc3.build(story3)
    print("SBC PDFs generated.")


def generate_x12_edi_samples():
    x12_dir = os.path.join(DATA_DIR, "claims_x12")
    os.makedirs(x12_dir, exist_ok=True)

    # 1. 837P Professional Claim Sample (X12 EDI)
    edi_837p = (
        "ISA*00*          *00*          *ZZ*SUBMITTER1     *ZZ*PRICINGHUB     *260115*1200*^*00501*000000001*0*P*:~\n"
        "GS*HC*SUBMITTER1*PRICINGHUB*20260115*1200*1*X*005010X222A1~\n"
        "ST*837*0001*005010X222A1~\n"
        "BHT*0019*00*CLM-COMM-PROF-001*20260115*1200*CH~\n"
        "NM1*41*2*REGIONAL MEDICAL GROUP*****XX*1982730192~\n"
        "NM1*40*2*PRICING HUB COMMERCIAL*****46*PAYER001~\n"
        "HL*1**20*1~\n"
        "HL*2*1*22*0~\n"
        "NM1*IL*1*MEMBER*ONE****MI*MEM-COMM-001~\n"
        "CLM*CLM-COMM-PROF-001*250.00***11:B:1*Y*A*Y*Y~\n"
        "HI*BK:I10*BF:E119~\n"
        "LX*1~\n"
        "SV1*HC:99214*250.00*UN*1***1~\n"
        "DTP*472*D8*20260115~\n"
        "SE*13*0001~\n"
        "GE*1*1~\n"
        "IEA*1*000000001~"
    )
    with open(os.path.join(x12_dir, "sample_837p_professional.x12"), "w") as f:
        f.write(edi_837p)

    # 2. 837I Facility Inpatient Claim Sample (X12 EDI)
    edi_837i = (
        "ISA*00*          *00*          *ZZ*HOSPITAL1      *ZZ*PRICINGHUB     *260115*1200*^*00501*000000002*0*P*:~\n"
        "GS*HC*HOSPITAL1*PRICINGHUB*20260115*1200*2*X*005010X223A2~\n"
        "ST*837*0002*005010X223A2~\n"
        "BHT*0019*00*CLM-COMM-FAC-026*20260115*1200*CH~\n"
        "NM1*41*2*METROPOLITAN HOSPITAL*****XX*1548291034~\n"
        "NM1*40*2*PRICING HUB COMMERCIAL*****46*PAYER001~\n"
        "HL*1**20*1~\n"
        "HL*2*1*22*0~\n"
        "NM1*IL*1*MEMBER*TWO****MI*MEM-COMM-001~\n"
        "CLM*CLM-COMM-FAC-026*35000.00***11:A:1*Y*A*Y*Y~\n"
        "DTP*435*D8*20260110~\n"
        "DTP*096*D8*20260114~\n"
        "HI*BK:M1611*BF:I10*DR:470~\n"
        "LX*1~\n"
        "SV2*0110*HC:0001*35000.00*UN*4~\n"
        "DTP*472*RD8*20260110-20260114~\n"
        "SE*15*0002~\n"
        "GE*1*2~\n"
        "IEA*1*000000002~"
    )
    with open(os.path.join(x12_dir, "sample_837i_facility.x12"), "w") as f:
        f.write(edi_837i)

    # 3. 837D Dental Excluded Claim Sample (X12 EDI)
    edi_837d = (
        "ISA*00*          *00*          *ZZ*DENTALCLINIC   *ZZ*PRICINGHUB     *260115*1200*^*00501*000000003*0*P*:~\n"
        "GS*HC*DENTALCLINIC*PRICINGHUB*20260115*1200*3*X*005010X224A2~\n"
        "ST*837*0003*005010X224A2~\n"
        "BHT*0019*00*CLM-DENT-EXCLUDED-01*20260115*1200*CH~\n"
        "NM1*41*2*REGIONAL DENTAL CLINIC*****XX*1982730192~\n"
        "CLM*CLM-DENT-EXCLUDED-01*85.00***11:A:1*Y*A*Y*Y~\n"
        "SV3*AD:D0120*85.00**1~\n"
        "SE*7*0003~\n"
        "GE*1*3~\n"
        "IEA*1*000000003~"
    )
    with open(os.path.join(x12_dir, "sample_837d_dental_excluded.x12"), "w") as f:
        f.write(edi_837d)

    # 4. JSON output structure mimicking x12-to-json-parser skill
    parsed_x12 = {
        "interchange": {"sender": "SUBMITTER1", "receiver": "PRICINGHUB", "control_number": "000000001"},
        "functional_groups": [{"functional_id": "HC", "version": "005010X222A1"}],
        "claim_type": "PROFESSIONAL",
        "line_of_business": "COMMERCIAL",
        "member_id": "MEM-COMM-001",
        "billing_provider_npi": "1982730192",
        "rendering_provider_npi": "1982730192",
        "loop_2300": {
            "claim_id": "CLM-X12-PARSED-001",
            "total_charge_amount": 250.00,
            "place_of_service": "11",
            "principal_diagnosis": "I10",
        },
        "loop_2400": [
            {
                "line_number": 1,
                "sv1": {
                    "procedure_code": "99214",
                    "charge_amount": 250.00,
                    "units": 1.0,
                    "modifiers": [],
                },
                "service_date": "2026-01-15",
            }
        ],
    }
    with open(os.path.join(x12_dir, "sample_parsed_x12_loops.json"), "w") as f:
        json.dump(parsed_x12, f, indent=2)

    print("X12 EDI and parsed loop samples generated.")


def generate_combined_integration_test_file():
    integ_dir = os.path.join(DATA_DIR, "integration_tests")
    os.makedirs(integ_dir, exist_ok=True)

    rows = [
        {
            "test_case_id": "COG-INT-001",
            "member_id": "MEM-COMM-001",
            "provider_id": "1982730192",
            "service_type": "PROFESSIONAL",
            "service_date": "2026-01-15",
            "principal_diagnosis": "M23.22",
            "procedure_code": "29881",
            "revenue_code": "",
            "drg_code": "",
            "billed_amount": 3500.00,
            "expected_lob": "COMMERCIAL",
            "member_pick_status": "ACTIVE_ELIGIBLE",
            "benefit_tier": "TIER_1_IN_NETWORK",
            "deductible_remaining": 500.00,
            "resolved_contract_id": "CTR-COMM-2026",
            "pricing_methodology": "FEE_SCHEDULE",
            "expected_allowable": 1250.00,
            "expected_disposition": "PAID",
            "audit_citation": "Section 3.1 - Standard Fee Schedule / Exhibit A",
        },
        {
            "test_case_id": "COG-INT-002",
            "member_id": "MEM-MED-042",
            "provider_id": "1649201948",
            "service_type": "FACILITY_INPATIENT",
            "service_date": "2026-01-12",
            "principal_diagnosis": "M16.11",
            "procedure_code": "0001",
            "revenue_code": "0110",
            "drg_code": "470",
            "billed_amount": 25000.00,
            "expected_lob": "MEDICARE",
            "member_pick_status": "ACTIVE_ELIGIBLE",
            "benefit_tier": "TIER_1_IN_NETWORK",
            "deductible_remaining": 0.00,
            "resolved_contract_id": "CTR-MED-ADV-2026",
            "pricing_methodology": "DRG_CASE_RATE",
            "expected_allowable": 14040.00,
            "expected_disposition": "PAID",
            "audit_citation": "Section 3.5 - CMS IPPS DRG Methodology",
        },
        {
            "test_case_id": "COG-INT-003",
            "member_id": "MEM-MCD-089",
            "provider_id": "1382910492",
            "service_type": "PROFESSIONAL",
            "service_date": "2026-01-15",
            "principal_diagnosis": "J45.909",
            "procedure_code": "99214",
            "revenue_code": "",
            "drg_code": "",
            "billed_amount": 160.00,
            "expected_lob": "MEDICAID",
            "member_pick_status": "ACTIVE_ELIGIBLE",
            "benefit_tier": "TIER_1_IN_NETWORK",
            "deductible_remaining": 0.00,
            "resolved_contract_id": "CTR-MCD-MCO-2026",
            "pricing_methodology": "FEE_SCHEDULE",
            "expected_allowable": 105.00,
            "expected_disposition": "PAID",
            "audit_citation": "Section 1.4 - State Medicaid Fee Base",
        },
        {
            "test_case_id": "COG-INT-004",
            "member_id": "MEM-COMM-001",
            "provider_id": "1548291034",
            "service_type": "FACILITY_OUTPATIENT",
            "service_date": "2026-01-15",
            "principal_diagnosis": "K29.00",
            "procedure_code": "45378",
            "revenue_code": "0360",
            "drg_code": "",
            "billed_amount": 8000.00,
            "expected_lob": "COMMERCIAL",
            "member_pick_status": "ACTIVE_ELIGIBLE",
            "benefit_tier": "TIER_1_IN_NETWORK",
            "deductible_remaining": 500.00,
            "resolved_contract_id": "CTR-COMM-2026",
            "pricing_methodology": "PERCENT_OF_CHARGES",
            "expected_allowable": 5200.00,
            "expected_disposition": "PAID",
            "audit_citation": "Section 3.2 - Percent of Billed Charges",
        },
        {
            "test_case_id": "COG-INT-005",
            "member_id": "MEM-COMM-001",
            "provider_id": "1982730192",
            "service_type": "PROFESSIONAL",
            "service_date": "2026-01-15",
            "principal_diagnosis": "E11.9",
            "procedure_code": "99000",
            "revenue_code": "",
            "drg_code": "",
            "billed_amount": 30.00,
            "expected_lob": "COMMERCIAL",
            "member_pick_status": "ACTIVE_ELIGIBLE",
            "benefit_tier": "TIER_1_IN_NETWORK",
            "deductible_remaining": 500.00,
            "resolved_contract_id": "CTR-COMM-2026",
            "pricing_methodology": "BUNDLED_PACKAGE",
            "expected_allowable": 0.00,
            "expected_disposition": "DENIED",
            "audit_citation": "PAYER-RP-018, Paragraph 5.1 (CARC CO-97)",
        },
    ]

    csv_path = os.path.join(integ_dir, "cog_integration_test_file.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = os.path.join(integ_dir, "cog_integration_test_file.json")
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)

    print("Combined integration test file (CSV & JSON) generated.")


def main():
    print("Generating complete synthetic documentation package (PDFs, X12 EDI, Integration Test File)...")
    generate_contract_pdfs()
    generate_policy_pdfs()
    generate_sbc_pdfs()
    generate_x12_edi_samples()
    generate_combined_integration_test_file()
    print("All supplementary synthetic test artifacts generated successfully!")


if __name__ == "__main__":
    main()
