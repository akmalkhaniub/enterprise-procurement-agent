import re
from typing import List
from src.schemas import ContractAnalysis, ContractClause, RiskLevel


class ContractAnalysisAgent:
    """Agent responsible for parsing vendor contracts and extracting risk clauses."""

    def analyze_contract(self, vendor_name: str, contract_title: str, contract_text: str, annual_value_usd: float) -> ContractAnalysis:
        clauses: List[ContractClause] = []

        # 1. Liability cap check
        if re.search(r"liability\s+shall\s+not\s+exceed", contract_text, re.IGNORECASE):
            match = re.search(r"liability\s+shall\s+not\s+exceed\s+\$?([0-9,]+)", contract_text, re.IGNORECASE)
            cap_val = match.group(1) if match else "specified amount"
            clauses.append(ContractClause(
                category="Liability",
                clause_text=f"Liability capped at ${cap_val}",
                risk_level=RiskLevel.LOW,
                flags=["standard_cap"],
            ))
        elif re.search(r"unlimited\s+liability", contract_text, re.IGNORECASE):
            clauses.append(ContractClause(
                category="Liability",
                clause_text="Unlimited liability clause detected.",
                risk_level=RiskLevel.CRITICAL,
                flags=["unlimited_liability_exposure"],
            ))

        # 2. SLA check
        if re.search(r"99\.95%|99\.9%|sla", contract_text, re.IGNORECASE):
            clauses.append(ContractClause(
                category="SLA",
                clause_text="Service Level Agreement promises 99.9%+ uptime.",
                risk_level=RiskLevel.LOW,
                flags=["uptime_guarantee"],
            ))
        else:
            clauses.append(ContractClause(
                category="SLA",
                clause_text="No explicit uptime SLA guarantee found.",
                risk_level=RiskLevel.MEDIUM,
                flags=["missing_sla"],
            ))

        # 3. Data Privacy check
        if re.search(r"gdpr|hipaa|soc\s*2|data\s+protection", contract_text, re.IGNORECASE):
            clauses.append(ContractClause(
                category="DataPrivacy",
                clause_text="Data protection standards explicitly referenced.",
                risk_level=RiskLevel.LOW,
                flags=["data_compliance_ok"],
            ))
        else:
            clauses.append(ContractClause(
                category="DataPrivacy",
                clause_text="Missing explicit GDPR/SOC2 data protection clauses.",
                risk_level=RiskLevel.HIGH,
                flags=["missing_privacy_clause"],
            ))

        return ContractAnalysis(
            vendor_name=vendor_name,
            contract_title=contract_title,
            annual_value_usd=annual_value_usd,
            clauses=clauses,
        )
