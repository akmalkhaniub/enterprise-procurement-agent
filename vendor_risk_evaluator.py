"""
Vendor Risk & Compliance Evaluator Engine for Enterprise Procurement Agent
Evaluates procurement vendor quotes across ESG score, delivery SLA, financial stability, and cost.
"""
from typing import Dict, Any, List

class VendorRiskEvaluator:
    """Evaluates vendor risk and compliance score."""

    @staticmethod
    def evaluate_vendor(
        vendor_name: str,
        unit_price: float,
        esg_rating: float,          # 0..100
        on_time_delivery_pct: float, # 0..100
        financial_credit_score: float # 0..100
    ) -> Dict[str, Any]:
        """Compute composite vendor risk score and approval recommendation."""
        
        # Weighted composite score
        price_score = max(0, 100 - (unit_price * 0.5))
        esg_weight = esg_rating * 0.25
        sla_weight = on_time_delivery_pct * 0.35
        financial_weight = financial_credit_score * 0.25
        price_weight = price_score * 0.15

        composite_score = round(esg_weight + sla_weight + financial_weight + price_weight, 1)

        risk_level = "LOW_RISK" if composite_score >= 75 else "MEDIUM_RISK" if composite_score >= 55 else "HIGH_RISK"
        recommendation = "APPROVED" if risk_level == "LOW_RISK" else "CONDITIONAL_APPROVAL" if risk_level == "MEDIUM_RISK" else "REJECTED"

        return {
            "vendor_name": vendor_name,
            "composite_score": composite_score,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "metrics": {
                "unit_price": unit_price,
                "esg_rating": esg_rating,
                "on_time_delivery_pct": on_time_delivery_pct,
                "financial_credit_score": financial_credit_score
            }
        }
