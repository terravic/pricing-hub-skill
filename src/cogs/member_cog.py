"""Member Pick Cog Simulator."""

import json
import os
from typing import Dict, Any, Optional


class MemberPickCog:
    """Resolves member eligibility, plan enrollment, and line of business."""

    def __init__(self, benefits_file: str = "data/benefits/member_benefits_accumulators.json"):
        self.members: Dict[str, Any] = {}
        if os.path.exists(benefits_file):
            with open(benefits_file, "r") as f:
                self.members = json.load(f)

    def resolve_member(self, member_id: str) -> Optional[Dict[str, Any]]:
        record = self.members.get(member_id)
        if not record or not record.get("active", False):
            return None
        return {
            "member_id": record["member_id"],
            "line_of_business": record["line_of_business"],
            "plan_name": record["plan_name"],
            "eligibility_status": "ACTIVE",
        }
