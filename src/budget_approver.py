from typing import Dict
from src.schemas import ProcurementDecision, ApprovalStatus, VendorRiskScore, ContractAnalysis, RiskLevel


class BudgetApprovalAgent:
    """Agent evaluating departmental budget thresholds & routing procurement approval decisions."""

    DEPARTMENT_BUDGETS: Dict[str, float] = {
        "Engineering": 250000.0,
        "Marketing": 100000.0,
        "Operations": 150000.0,
        "Security": 300000.0,
    }

    def evaluate_procurement(
        self,
        department: str,
        requested_amount_usd: float,
        analysis: ContractAnalysis,
        risk: VendorRiskScore,
    ) -> ProcurementDecision:
        limit = self.DEPARTMENT_BUDGETS.get(department, 50000.0)

        if risk.risk_level == RiskLevel.CRITICAL:
            return ProcurementDecision(
                vendor_name=analysis.vendor_name,
                contract_title=analysis.contract_title,
                requested_amount_usd=requested_amount_usd,
                department=department,
                status=ApprovalStatus.REJECTED,
                approval_reason=f"Procurement rejected due to CRITICAL vendor risk score ({risk.overall_risk_score}/100).",
                risk_score=risk,
                contract_analysis=analysis,
            )

        if requested_amount_usd > limit:
            return ProcurementDecision(
                vendor_name=analysis.vendor_name,
                contract_title=analysis.contract_title,
                requested_amount_usd=requested_amount_usd,
                department=department,
                status=ApprovalStatus.REQUIRES_EXECUTIVE_REVIEW,
                approval_reason=f"Requested amount ${requested_amount_usd:,.2f} exceeds departmental budget limit (${limit:,.2f}). Escalated to CFO/Executive Review.",
                risk_score=risk,
                contract_analysis=analysis,
            )

        return ProcurementDecision(
            vendor_name=analysis.vendor_name,
            contract_title=analysis.contract_title,
            requested_amount_usd=requested_amount_usd,
            department=department,
            status=ApprovalStatus.APPROVED,
            approval_reason=f"Approved. Amount within ${limit:,.2f} budget limit and vendor risk posture acceptable ({risk.overall_risk_score}/100).",
            risk_score=risk,
            contract_analysis=analysis,
        )
