"""Tests for Real-Time Pricing Load Monitoring, Stalled Bottleneck Tracking, and SLAs."""

import pytest
from src.monitoring.load_tracker import PricingLoadTracker
from src.monitoring.bottleneck_analyzer import BottleneckAnalyzer
from src.models.monitoring_models import LoadStatus, BottleneckReason, AlertSeverity


def test_load_lifecycle_outstanding_to_loaded():
    tracker = PricingLoadTracker(target_sla_seconds=7200)
    record = tracker.register_load("CTR-COMM-2026", "COMMERCIAL", 100, "LOAD-TEST-01")

    assert record.status == LoadStatus.OUTSTANDING
    assert record.completion_percentage == 0.0

    # Process 50 claims
    tracker.update_progress("LOAD-TEST-01", loaded_increment=50, elapsed_seconds=1200)
    rec = tracker.loads["LOAD-TEST-01"]
    assert rec.status == LoadStatus.OUTSTANDING
    assert rec.completion_percentage == 50.0

    # Process remaining 50 claims
    tracker.update_progress("LOAD-TEST-01", loaded_increment=50, elapsed_seconds=2400)
    rec = tracker.loads["LOAD-TEST-01"]
    assert rec.status == LoadStatus.LOADED
    assert rec.completion_percentage == 100.0


def test_stalled_load_detection_and_alerting():
    tracker = PricingLoadTracker(target_sla_seconds=7200)
    tracker.register_load("CTR-MCD-MCO-2026", "MEDICAID", 200, "LOAD-TEST-STALL")

    # Update with unmapped provider NPI
    tracker.update_progress("LOAD-TEST-STALL", loaded_increment=5, elapsed_seconds=1000, provider_registered=False)
    rec = tracker.loads["LOAD-TEST-STALL"]

    assert rec.status == LoadStatus.STALLED
    assert rec.bottleneck_reason == BottleneckReason.PROVIDER_NPI_UNMAPPED
    assert "not mapped" in rec.bottleneck_details

    # Assert critical alert was emitted
    alerts = tracker.dispatcher.get_active_alerts(severity=AlertSeverity.CRITICAL)
    assert len(alerts) >= 1
    assert alerts[0].alert_type == "STALLED_LOAD_DETECTED"
    assert alerts[0].load_id == "LOAD-TEST-STALL"


def test_sla_breach_detection():
    tracker = PricingLoadTracker(target_sla_seconds=3600)  # 1 hour SLA
    tracker.register_load("CTR-MED-ADV-2026", "MEDICARE", 500, "LOAD-TEST-SLA")

    # Update with elapsed time of 4000s (> 3600s)
    tracker.update_progress("LOAD-TEST-SLA", loaded_increment=100, elapsed_seconds=4000)
    rec = tracker.loads["LOAD-TEST-SLA"]

    assert rec.is_sla_breached is True
    alerts = [a for a in tracker.dispatcher.alerts if a.alert_type == "SLA_BREACH_WARNING"]
    assert len(alerts) >= 1
