from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit_technical_report_evidence import (
    CRITERIA_DEFINITIONS,
    audit_technical_report_evidence,
)

ROOT = Path(__file__).resolve().parents[1]


def test_technical_report_evidence_audit_passes():
    results = audit_technical_report_evidence(ROOT)
    assert results["overall_status"] == "PASS"
    assert results["compliant_criteria"] == 14
    assert results["total_criteria"] == 14
    assert results["missing_files"] == []


def test_technical_report_criteria_completeness():
    results = audit_technical_report_evidence(ROOT)
    for criterion_key, defn in CRITERIA_DEFINITIONS.items():
        assert criterion_key in results["criteria"]
        c_res = results["criteria"][criterion_key]
        assert c_res["status"] == "PASS"
        assert len(c_res["failures"]) == 0
        assert len(c_res["checked_files"]) == len(defn["required_files"])


def test_technical_report_audit_cli():
    script_path = ROOT / "scripts" / "audit_technical_report_evidence.py"
    output = subprocess.check_output(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        text=True,
    )
    assert "Overall Status: PASS" in output
    assert "Compliant Criteria: 14 / 14" in output
