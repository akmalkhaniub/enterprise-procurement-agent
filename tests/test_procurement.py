import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.orchestrator import ProcurementOrchestrator
from src.schemas import ApprovalStatus, RiskLevel


def test_procurement_approval_success():
    orchestrator = ProcurementOrchestrator()
    contract_text = "Standard SaaS terms. Liability shall not exceed $100,000. 99.95% uptime SLA guaranteed. Fully GDPR and SOC2 compliant."
    decision = orchestrator.process_vendor_intake(
        vendor_name="Datadog Cloud",
        contract_title="Observability License",
        contract_text=contract_text,
        requested_amount_usd=45000.0,
        department="Engineering",
        soc2_certified=True,
        gdpr_compliant=True,
    )

    assert decision.status == ApprovalStatus.APPROVED
    assert decision.risk_score.risk_level == RiskLevel.LOW
    assert decision.risk_score.overall_risk_score >= 80.0


def test_procurement_executive_review_needed():
    orchestrator = ProcurementOrchestrator()
    contract_text = "Enterprise cloud terms. Liability shall not exceed $1,000,000. SOC2 compliant."
    decision = orchestrator.process_vendor_intake(
        vendor_name="Snowflake Data Warehouse",
        contract_title="Enterprise Data Warehouse",
        contract_text=contract_text,
        requested_amount_usd=500000.0,  # Exceeds Engineering budget ($250k)
        department="Engineering",
        soc2_certified=True,
        gdpr_compliant=True,
    )

    assert decision.status == ApprovalStatus.REQUIRES_EXECUTIVE_REVIEW
    assert "exceeds departmental budget limit" in decision.approval_reason


def test_procurement_rejection_critical_risk():
    orchestrator = ProcurementOrchestrator()
    contract_text = "Vendor assumes unlimited liability. No privacy clauses."
    decision = orchestrator.process_vendor_intake(
        vendor_name="Untrusted Cloud Services",
        contract_title="Unverified Storage Contract",
        contract_text=contract_text,
        requested_amount_usd=10000.0,
        department="Marketing",
        soc2_certified=False,
        gdpr_compliant=False,
    )

    assert decision.status == ApprovalStatus.REJECTED
    assert decision.risk_score.risk_level == RiskLevel.CRITICAL
