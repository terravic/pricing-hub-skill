#!/usr/bin/env python3
"""CLI utility for real-time Pricing Load monitoring and bottleneck tracking."""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.monitoring.load_tracker import PricingLoadTracker
from src.models.monitoring_models import BottleneckReason, LoadStatus


def main():
    print("=================================================================")
    print("        PRICING HUB: REAL-TIME PRICING LOAD MONITOR             ")
    print("=================================================================\n")

    tracker = PricingLoadTracker(target_sla_seconds=7200)

    # Simulate 5 concurrent migration loads
    print("[*] Initializing Pricing Pipeline Loads...")
    l1 = tracker.register_load("CTR-COMM-2026", "COMMERCIAL", 1000, "LOAD-COMM-HMO-01")
    l2 = tracker.register_load("CTR-MED-ADV-2026", "MEDICARE", 750, "LOAD-MED-CHOICE-02")
    l3 = tracker.register_load("CTR-MCD-MCO-2026", "MEDICAID", 500, "LOAD-MCD-COMM-03")
    l4 = tracker.register_load("CTR-COMM-PPO-2026", "COMMERCIAL", 1200, "LOAD-COMM-PPO-04")
    l5 = tracker.register_load("CTR-MED-SNP-2026", "MEDICARE", 400, "LOAD-MED-SNP-05")

    # Update states:
    # Load 1 completes 100%
    tracker.update_progress("LOAD-COMM-HMO-01", loaded_increment=1000, elapsed_seconds=2100)

    # Load 2 is actively progressing (OUTSTANDING)
    tracker.update_progress("LOAD-MED-CHOICE-02", loaded_increment=450, elapsed_seconds=3600)

    # Load 3 stalled due to unmapped provider NPI
    tracker.update_progress("LOAD-MCD-COMM-03", loaded_increment=25, elapsed_seconds=4200, provider_registered=False)

    # Load 4 stalled due to rate card date overlap
    tracker.update_progress("LOAD-COMM-PPO-04", loaded_increment=0, elapsed_seconds=5000, has_date_conflict=True)

    # Load 5 stalled due to validation failure rate spike (>2%)
    tracker.update_progress("LOAD-MED-SNP-05", loaded_increment=100, failed_increment=20, elapsed_seconds=1800)

    summary = tracker.get_pipeline_summary()

    print("-----------------------------------------------------------------")
    print("                    PIPELINE HEALTH OVERVIEW                     ")
    print("-----------------------------------------------------------------")
    counts = summary["status_counts"]
    print(f"Total Loads Tracked : {summary['total_loads']}")
    print(f"  [+] LOADED        : {counts['LOADED']} (Validated & Ready)")
    print(f"  [*] OUTSTANDING   : {counts['OUTSTANDING']} (In Progress / Adjudicating)")
    print(f"  [!] STALLED       : {counts['STALLED']} (Blocked / Bottleneck Detected)")
    print(f"SLA Breaches        : {summary['sla_breaches']}")
    print(f"Active Alerts       : {summary['active_alerts_count']}")

    print("\n-----------------------------------------------------------------")
    print("                    REAL-TIME LOAD STATUS TABLE                  ")
    print("-----------------------------------------------------------------")
    print(f"{'Load ID':<20} | {'LOB':<10} | {'Status':<12} | {'Progress':<10} | {'ETA':<20}")
    print("-" * 80)
    for lid, rec in tracker.loads.items():
        status_disp = rec.status.value
        progress_disp = f"{rec.completion_percentage}%"
        eta_disp = rec.estimated_completion_time or "N/A"
        print(f"{rec.load_id:<20} | {rec.line_of_business:<10} | {status_disp:<12} | {progress_disp:<10} | {eta_disp:<20}")

    if summary["stalled_bottlenecks"]:
        print("\n-----------------------------------------------------------------")
        print("                  STALLED BOTTLENECK DIAGNOSTICS                 ")
        print("-----------------------------------------------------------------")
        for idx, b in enumerate(summary["stalled_bottlenecks"], 1):
            print(f"{idx}. Load: {b['load_id']} | Contract: {b['contract_id']}")
            print(f"   Reason : {b['reason']}")
            print(f"   Details: {b['details']}")
            print(f"   Elapsed: {b['elapsed_hours']} hours\n")

    if tracker.dispatcher.alerts:
        print("-----------------------------------------------------------------")
        print("                     ACTIVE ALERT DISPATCHES                     ")
        print("-----------------------------------------------------------------")
        for a in tracker.dispatcher.alerts:
            print(f"[{a.severity.value}] {a.alert_type} ({a.timestamp}):")
            print(f"  {a.message}")
            if a.action_required:
                print(f"  >> Action Required: {a.action_required}")
            print()

    print("=================================================================")
    print("MONITORING CYCLE COMPLETED.")
    print("=================================================================")

    # Automatically create / update dashboard with pipeline monitoring status
    from src.ui.dashboard_generator import generate_dashboard, print_dashboard_banner
    generate_dashboard(task_type="monitoring")
    print_dashboard_banner(task_name="Pipeline Migration Monitoring")


if __name__ == "__main__":
    main()
