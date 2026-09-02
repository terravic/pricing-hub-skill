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
) -> str:
    """Ensures src/ui/dashboard.html is generated and adapted to the specific task executed.
    Dynamically adjusts default active tab, task execution banner, and sample presets
    while preserving the complete unified 6-tab system.
    """
    rel_path = os.path.relpath(DASHBOARD_PATH, PROJECT_ROOT)

    if not os.path.exists(DASHBOARD_PATH):
        raise FileNotFoundError(f"Dashboard template not found at {DASHBOARD_PATH}")

    with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Determine target tab and task context
    target_tab = "tab-ingestion"
    task_title = "Unified Dashboard"
    badge_text = "Engine Online"

    if claims_file and claims_file.endswith((".x12", ".edi")):
        target_tab = "tab-verification"
        task_title = f"Task: Single Claim .X12 Ingestion &bull; Target: {claims_file}"
        badge_text = "X12 Processed"
    elif claims_file and "golden" in claims_file:
        target_tab = "tab-verification"
        task_title = f"Task: Batch Parity Verification &bull; Target: {claims_file}"
        badge_text = "Parity Verified"
    elif task_type == "ingestion":
        target_tab = "tab-ingestion"
        task_title = "Task: Contract & Reimbursement Policy Ingestion"
        badge_text = "Ingested & Indexed"
    elif task_type == "monitoring":
        target_tab = "tab-monitoring"
        task_title = "Task: Pipeline Migration & Bottleneck Monitoring"
        badge_text = "Pipeline Tracked"
    elif task_type == "pricing":
        target_tab = "tab-pricing"
        task_title = "Task: Interactive Adjudicator & Modifier Calculation"
        badge_text = "Adjudication Tested"
    elif task_type in ("cog", "cogs"):
        target_tab = "tab-cogs"
        task_title = "Task: Multi-Cog Handshake Pipeline Simulation"
        badge_text = "Handshake Verified"

    # 1. Update active tab buttons
    content = re.sub(r'<button class="tab-btn active"', r'<button class="tab-btn"', content)
    target_btn = f'<button class="tab-btn" onclick="switchTab(\'{target_tab}\')">'
    active_btn = f'<button class="tab-btn active" onclick="switchTab(\'{target_tab}\')">'
    content = content.replace(target_btn, active_btn)

    # 2. Update active tab-panel
    content = re.sub(r'<div id="(tab-[a-z0-9]+)" class="tab-panel active"', r'<div id="\1" class="tab-panel"', content)
    target_panel = f'<div id="{target_tab}" class="tab-panel"'
    active_panel = f'<div id="{target_tab}" class="tab-panel active"'
    content = content.replace(target_panel, active_panel)

    # 3. Update task execution banner
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

    # 4. If an X12 sample was passed, update default select option and load in UI
    if claims_file and claims_file.endswith((".x12", ".edi")):
        sample_key = "837p"
        if "837i" in claims_file or "facility" in claims_file:
            sample_key = "837i"
        elif "837d" in claims_file or "dental" in claims_file:
            sample_key = "837d"
        content = re.sub(r'<option value="([0-9a-zA-Z_-]+)" selected>', r'<option value="\1">', content)
        content = re.sub(rf'<option value="{sample_key}">', rf'<option value="{sample_key}" selected>', content)
        content = re.sub(
            r"loadClaimItem\('[0-9a-zA-Z_-]+', false\);",
            f"loadClaimItem('{sample_key}', false);",
            content
        )

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
