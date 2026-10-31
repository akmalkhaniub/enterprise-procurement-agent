import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_EXECUTIVE_REVIEW = "requires_executive_review"


class ContractClause(BaseModel):
    category: str  # SLA, Liability, DataPrivacy, Termination, PaymentTerms
    clause_text: str
    risk_level: RiskLevel
    flags: List[str] = Field(default_factory=list)


class ContractAnalysis(BaseModel):
    vendor_name: str
    contract_title: str
    annual_value_usd: float
    clauses: List[ContractClause] = Field(default_factory=list)
    extracted_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class VendorRiskScore(BaseModel):
    vendor_name: str
    soc2_compliant: bool
    gdpr_compliant: bool
    data_encryption_at_rest: bool
    overall_risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    recommendations: List[str] = Field(default_factory=list)


class ProcurementDecision(BaseModel):
    vendor_name: str
    contract_title: str
    requested_amount_usd: float
    department: str
    status: ApprovalStatus
    approval_reason: str
    risk_score: VendorRiskScore
    contract_analysis: ContractAnalysis
