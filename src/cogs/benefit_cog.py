"""Benefit Accumulator Cog Simulator."""

import json
import os
from typing import Dict, Any, Optional


class BenefitAccumulatorCog:
    """Calculates member benefit cost-sharing, deductibles remaining, and network tier."""

    def __init__(self, benefits_file: str = "data/benefits/member_benefits_accumulators.json"):
        self.members: Dict[str, Any] = {}
        if os.path.exists(benefits_file):
            with open(benefits_file, "r") as f:
                self.members = json.load(f)

    def evaluate_benefits(self, member_id: str, is_in_network: bool = True) -> Optional[Dict[str, Any]]:
        record = self.members.get(member_id)
        if not record:
            return None

        deductible_rem = max(0.0, record.get("individual_deductible", 0.0) - record.get("deductible_met", 0.0))
        tier = "TIER_1" if is_in_network else "OUT_OF_NETWORK"

        return {
            "member_id": member_id,
            "in_network_tier": tier,
            "deductible_remaining": round(deductible_rem, 2),
            "copay_pcp": record.get("copay_pcp", 0.0),
            "copay_specialist": record.get("copay_specialist", 0.0),
            "coinsurance_percentage": record.get("coinsurance_percentage", 0.0),
            "oop_remaining": max(0.0, record.get("out_of_pocket_max", 0.0) - record.get("oop_accumulated", 0.0)),
        }
