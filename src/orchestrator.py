from src.schemas import ProcurementDecision
from src.contract_analyzer import ContractAnalysisAgent
from src.risk_assessor import VendorRiskAgent
from src.budget_approver import BudgetApprovalAgent


class ProcurementOrchestrator:
    """Master orchestrator executing the 3-stage enterprise procurement workflow."""

    def __init__(self):
        self.contract_agent = ContractAnalysisAgent()
        self.risk_agent = VendorRiskAgent()
        self.budget_agent = BudgetApprovalAgent()

    def process_vendor_intake(
        self,
        vendor_name: str,
        contract_title: str,
        contract_text: str,
        requested_amount_usd: float,
        department: str,
        soc2_certified: bool = True,
        gdpr_compliant: bool = True,
    ) -> ProcurementDecision:
        # Stage 1: Contract Clause Extraction
        analysis = self.contract_agent.analyze_contract(vendor_name, contract_title, contract_text, requested_amount_usd)

        # Stage 2: Vendor Risk & Security Assessment
        risk = self.risk_agent.assess_vendor_risk(analysis, soc2_certified, gdpr_compliant)

        # Stage 3: Department Budget Verification & Approval Routing
        decision = self.budget_agent.evaluate_procurement(department, requested_amount_usd, analysis, risk)

        return decision
