"""Dashboard Generator Utility for the Pricing Hub Skill.

Automatically adapts and updates the unified interactive dashboard at src/ui/dashboard.html
whenever a processing task (ingestion, verification, X12 parsing, or load monitoring) completes.
"""

import os
import re
from typing import Optional, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASHBOARD_PATH = os.path.join(PROJECT_ROOT, "src", "ui", "dashboard.html")


def generate_dashboard(
    results: Optional[Dict[str, Any]] = None,
    task_type: str = "general",
    claims_file: Optional[str] = None,
    input_file: Optional[str] = None,
    query_title: Optional[str] = None,
    custom_notes: Optional[str] = None,
) -> str:
    """Ensures output/dashboard.html is generated and adapted to ANY question,
    analysis, or unseen input file processed by the Pricing Hub skill.
    
    Dynamically adjusts default active tab, task execution banner, and sample presets
    to match the user's specific inquiry across all 5 unified dashboard modules.
    """
    if not os.path.exists(DASHBOARD_PATH):
        raise FileNotFoundError(f"Dashboard template not found at {DASHBOARD_PATH}")

    with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    effective_file = input_file or claims_file
    if effective_file:
        effective_file = os.path.normpath(effective_file)

    # Determine target tab and task context dynamically
    target_tab = "tab-ingestion"
    task_title = "Pricing Hub Process Inspector"
    badge_text = "Analysis Ready"

    # 1. File-based routing for unseen or provided files
    if effective_file and effective_file.endswith((".x12", ".edi")):
        target_tab = "tab-verification"
        task_title = f"Task: Claim .X12 Ingestion &bull; Target: {os.path.basename(effective_file)}"
        badge_text = "EDI Evaluated"
    elif effective_file and "golden" in effective_file:
        target_tab = "tab-verification"
        task_title = f"Task: Batch Parity Verification &bull; Target: {os.path.basename(effective_file)}"
        badge_text = "Parity Verified"
    elif effective_file and (effective_file.endswith(".pdf") or effective_file.endswith((".json", ".yaml", ".yml"))):
        target_tab = "tab-ingestion"
        file_base = os.path.basename(effective_file)
        if any(k in file_base.lower() for k in ["policy", "ncd", "lcd", "rule"]):
            task_title = f"Task: Clinical Policy Ingestion &bull; Target: {file_base}"
            badge_text = "Policy Parsed"
        else:
            task_title = f"Task: Provider Contract Ingestion &bull; Target: {file_base}"
            badge_text = "Contract Parsed"
    # 2. Topic/inquiry-based routing for arbitrary user questions
    elif any(k in task_type.lower() for k in ["price", "pricing", "adjudicat", "calculat", "modifier", "split", "fee"]):
        target_tab = "tab-pricing"
        task_title = query_title or "Task: Claim Pricing & Modifier Adjudication"
        badge_text = "Adjudication Tested"
    elif any(k in task_type.lower() for k in ["monitor", "bottleneck", "sla", "stalled", "pipeline", "load"]):
        target_tab = "tab-monitoring"
        task_title = query_title or "Task: Pipeline Migration & Bottleneck Monitoring"
        badge_text = "Pipeline Tracked"
    elif any(k in task_type.lower() for k in ["cog", "handshake", "inter-cog", "flow", "benefit", "member"]):
        target_tab = "tab-cogs"
        task_title = query_title or "Task: Multi-Cog Inter-Process Flow"
        badge_text = "Handshake Verified"
    elif any(k in task_type.lower() for k in ["claim", "x12", "edi", "verification", "parity", "audit"]):
        target_tab = "tab-verification"
        task_title = query_title or "Task: Claim Ingestion & Verification Parity"
        badge_text = "Claims Evaluated"
    elif any(k in task_type.lower() for k in ["contract", "policy", "ingest", "ncd", "lcd", "rule"]):
        target_tab = "tab-ingestion"
        task_title = query_title or "Task: Contract & Policy Ingestion Inspector"
        badge_text = "Rules Loaded"
    else:
        target_tab = "tab-ingestion"
        task_title = query_title or "Task: Pricing Hub Process Inspector"
        badge_text = "Analysis Ready"

    # User-specified query override
    if query_title:
        task_title = query_title
        badge_text = "Inquiry Analyzed"

    # Update active tab buttons
    content = re.sub(r'<button class="tab-btn active"', r'<button class="tab-btn"', content)
    target_btn = f'<button class="tab-btn" onclick="switchTab(\'{target_tab}\')">'
    active_btn = f'<button class="tab-btn active" onclick="switchTab(\'{target_tab}\')">'
    content = content.replace(target_btn, active_btn)

    # Update active tab-panel
    content = re.sub(r'<div id="(tab-[a-z0-9]+)" class="tab-panel active"', r'<div id="\1" class="tab-panel"', content)
    target_panel = f'<div id="{target_tab}" class="tab-panel"'
    active_panel = f'<div id="{target_tab}" class="tab-panel active"'
    content = content.replace(target_panel, active_panel)

    # Update task execution banner
    content = re.sub(
        r'<div id="taskBannerTitle"[^>]*>.*?</div>',
        f'<div id="taskBannerTitle" style="font-size: 13px; font-weight: 700; color: var(--text-main);">{task_title}</div>',
        content
    )
    content = re.sub(
        r'<span class="badge[^"]*" id="taskBannerBadge">.*?</span>',
        f'<span class="badge badge-success" id="taskBannerBadge">{badge_text}</span>',
        content
    )

    # If an X12 sample or unseen claim was passed, update default select option and load in UI
    if effective_file and effective_file.endswith((".x12", ".edi")):
        sample_key = "837p"
        if "837i" in effective_file or "facility" in effective_file:
            sample_key = "837i"
        elif "837d" in effective_file or "dental" in effective_file:
            sample_key = "837d"
        content = re.sub(r'<option value="([0-9a-zA-Z_-]+)" selected>', r'<option value="\1">', content)
        content = re.sub(rf'<option value="{sample_key}">', rf'<option value="{sample_key}" selected>', content)
        content = re.sub(
            r"loadClaimItem\('[0-9a-zA-Z_-]+', false\);",
            f"loadClaimItem('{sample_key}', false);",
            content
        )

    # Write to canonical component path
    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    # Output to primary skill output destination: output/dashboard.html
    output_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_dashboard = os.path.join(output_dir, "dashboard.html")
    with open(output_dashboard, "w", encoding="utf-8") as f:
        f.write(content)

    # Also keep root dashboard.html in sync for direct workspace file access and clicking
    root_dashboard = os.path.join(PROJECT_ROOT, "dashboard.html")
    with open(root_dashboard, "w", encoding="utf-8") as f:
        f.write(content)

    return "output/dashboard.html"


def print_dashboard_banner(task_name: str = "Requested Task", claims_file: Optional[str] = None):
    """Prints a standardized banner indicating the dashboard has been adapted and generated as a skill output."""
    view_hint = ""
    if claims_file:
        view_hint = " (Adapted to Tab 3: Verification Parity & Claim Inspector)"

    print("\n" + "=" * 65)
    print(f"[+] SKILL OUTPUT GENERATED FOR: {task_name.upper()}")
    print("=" * 65)
    print(f"[*] Primary Skill Output : output/dashboard.html{view_hint}")
    print(f"[*] Workspace Root File  : dashboard.html")
    print(f"[*] Source UI Component  : src/ui/dashboard.html")
    print("[*] Launch Local Server  : python3 scripts/launch_ui.py")
    print("[*] Copyable URL         : http://localhost:8080/dashboard.html")
    print("=" * 65 + "\n")
