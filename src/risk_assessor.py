from typing import List
from src.schemas import VendorRiskScore, RiskLevel, ContractAnalysis


class VendorRiskAgent:
    """Agent responsible for assessing vendor SOC2 compliance, privacy risk, and scoring overall risk posture."""

    def assess_vendor_risk(self, analysis: ContractAnalysis, soc2_certified: bool = True, gdpr_compliant: bool = True) -> VendorRiskScore:
        base_score = 90.0
        recs: List[str] = []

        if not soc2_certified:
            base_score -= 25.0
            recs.append("Mandate vendor submit SOC2 Type II audit report within 90 days.")

        if not gdpr_compliant:
            base_score -= 20.0
            recs.append("Require Data Processing Addendum (DPA) execution for EU data compliance.")

        for clause in analysis.clauses:
            if clause.risk_level == RiskLevel.CRITICAL:
                base_score -= 30.0
                recs.append(f"Critical clause flag: {clause.clause_text}")
            elif clause.risk_level == RiskLevel.HIGH:
                base_score -= 15.0
                recs.append(f"High risk flag: {clause.clause_text}")

        final_score = max(0.0, min(100.0, base_score))

        if final_score >= 80.0:
            level = RiskLevel.LOW
        elif final_score >= 60.0:
            level = RiskLevel.MEDIUM
        elif final_score >= 40.0:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        return VendorRiskScore(
            vendor_name=analysis.vendor_name,
            soc2_compliant=soc2_certified,
            gdpr_compliant=gdpr_compliant,
            data_encryption_at_rest=True,
            overall_risk_score=final_score,
            risk_level=level,
            recommendations=recs,
        )
