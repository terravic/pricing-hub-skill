"""Policy and Clinical Guideline Ingestion Parser."""

import json
import os
from typing import Dict, List, Any, Tuple, Optional
import yaml
from src.models.policy_models import PolicyRule, PolicyType, RuleAction


class PolicyParser:
    """Parses and indexes CMS LCD/NCD and Commercial Payer Reimbursement Policies."""

    def __init__(self):
        self.policies: Dict[str, PolicyRule] = {}
        self.code_to_policies: Dict[str, List[PolicyRule]] = {}

    def parse_file(self, file_path: str) -> Tuple[List[PolicyRule], List[str]]:
        """Parses a policy document JSON or YAML file."""
        errors: List[str] = []
        if not os.path.exists(file_path):
            return [], [f"Policy file not found: {file_path}"]

        try:
            with open(file_path, "r") as f:
                if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
        except Exception as e:
            return [], [f"Failed to parse policy file syntax: {str(e)}"]

        if isinstance(data, dict):
            data = [data]

        parsed_rules: List[PolicyRule] = []
        for idx, item in enumerate(data):
            required = ["policy_id", "policy_title", "policy_type", "paragraph_id", "rule_action", "citation_text"]
            item_errors = [f"Item {idx} missing '{k}'" for k in required if k not in item]
            if item_errors:
                errors.extend(item_errors)
                continue

            rule = PolicyRule.from_dict(item)
            self.policies[rule.policy_id] = rule
            parsed_rules.append(rule)

            # Index by target procedure codes
            for code in rule.target_procedure_codes:
                if code not in self.code_to_policies:
                    self.code_to_policies[code] = []
                self.code_to_policies[code].append(rule)

        return parsed_rules, errors

    def load_directory(self, dir_path: str) -> Dict[str, Any]:
        """Loads and indexes all policy files in a directory."""
        results = {"loaded_rules": 0, "failed_files": 0, "errors": {}}
        if not os.path.exists(dir_path):
            results["errors"]["dir"] = [f"Directory does not exist: {dir_path}"]
            return results

        for filename in sorted(os.listdir(dir_path)):
            if filename.endswith(".json") or filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(dir_path, filename)
                rules, errs = self.parse_file(filepath)
                if errs:
                    results["failed_files"] += 1
                    results["errors"][filename] = errs
                else:
                    results["loaded_rules"] += len(rules)

        return results

    def get_policy(self, policy_id: str) -> Optional[PolicyRule]:
        return self.policies.get(policy_id)

    def get_rules_for_procedure(self, procedure_code: str) -> List[PolicyRule]:
        return self.code_to_policies.get(procedure_code, [])
