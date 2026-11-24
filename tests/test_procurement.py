import math
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import agents
from src.orchestrator import ProcurementOrchestrator
from src.schemas import ApprovalStatus, RiskLevel


class InMemoryCosineVectorIndex:
    """Offline in-memory cosine similarity mock supporting Pinecone & Chroma query shapes."""

    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _embed(text: str) -> Counter:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        bigrams = [f"{tokens[i]}_{tokens[i + 1]}" for i in range(len(tokens) - 1)]
        return Counter(tokens + bigrams)

    @staticmethod
    def _cosine(a: Counter, b: Counter) -> float:
        if not a or not b:
            return 0.0
        dot = sum(a[k] * b.get(k, 0) for k in a)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def upsert(self, records: List[Dict[str, Any]]) -> int:
        for rec in records:
            text = rec["text"]
            self._records[rec["id"]] = {
                "id": rec["id"],
                "text": text,
                "metadata": rec.get("metadata", {}),
                "vector": self._embed(text),
            }
        return len(records)

    def query_pinecone(self, query_text: str, top_k: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        q_vec = self._embed(query_text)
        scored = []
        for rec in self._records.values():
            sim = self._cosine(q_vec, rec["vector"])
            scored.append(
                {
                    "id": rec["id"],
                    "score": round(sim, 6),
                    "metadata": {**rec["metadata"], "text": rec["text"]},
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return {"matches": scored[:top_k]}

    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, Any]:
        docs: List[List[str]] = []
        metas: List[List[Dict[str, Any]]] = []
        dists: List[List[float]] = []
        for q in query_texts:
            matches = self.query_pinecone(q, top_k=n_results)["matches"]
            docs.append([m["metadata"]["text"] for m in matches])
            metas.append([m["metadata"] for m in matches])
            dists.append([round(1.0 - m["score"], 6) for m in matches])
        return {"documents": docs, "metadatas": metas, "distances": dists}


@pytest.fixture
def mock_vector_index() -> InMemoryCosineVectorIndex:
    index = InMemoryCosineVectorIndex()
    index.upsert([
        {
            "id": "techcorp-msa",
            "text": (
                "TechCorp Inc. Master SaaS Agreement. Liability shall not exceed $100,000. "
                "99.95% uptime SLA guaranteed. Fully GDPR and SOC2 compliant."
            ),
            "metadata": {"vendor": "TechCorp Inc.", "department": "Engineering", "soc2": True, "gdpr": True},
        },
        {
            "id": "untrusted-cloud-tos",
            "text": (
                "Untrusted Cloud Services Terms. Vendor assumes unlimited liability. "
                "Best-effort availability with no SLA or data privacy clauses."
            ),
            "metadata": {"vendor": "Untrusted Cloud Services", "department": "Marketing", "soc2": False, "gdpr": False},
        },
        {
            "id": "datalake-dpa",
            "text": (
                "DataLake Analytics Enterprise SLA. 99.9% uptime SLA. "
                "Liability shall not exceed $500,000. SOC2 Type II and GDPR DPA executed."
            ),
            "metadata": {"vendor": "DataLake Analytics", "department": "Data", "soc2": True, "gdpr": True},
        },
    ])
    return index


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


def test_offline_cosine_vector_search_drives_contract_risk_evaluation(
    mock_vector_index: InMemoryCosineVectorIndex,
    monkeypatch: pytest.MonkeyPatch,
):
    # Verify Pinecone-style cosine similarity ranks TechCorp MSA highest for SLA + GDPR query
    pinecone_res = mock_vector_index.query_pinecone("TechCorp uptime SLA GDPR SOC2 compliance", top_k=2)
    assert pinecone_res["matches"][0]["id"] == "techcorp-msa"
    assert pinecone_res["matches"][0]["score"] > pinecone_res["matches"][1]["score"]

    # Verify agents.search_vendor_policies runs offline using monkeypatched collection
    monkeypatch.setattr(agents, "collection", mock_vector_index)
    policy_text = agents.search_vendor_policies.invoke({"query": "unlimited liability missing privacy"})
    assert "Untrusted Cloud Services" in policy_text

    # Feed top cosine match into ProcurementOrchestrator offline
    top_match = mock_vector_index.query_pinecone("TechCorp SaaS agreement", top_k=1)["matches"][0]
    orchestrator = ProcurementOrchestrator()
    decision = orchestrator.process_vendor_intake(
        vendor_name=top_match["metadata"]["vendor"],
        contract_title="TechCorp MSA",
        contract_text=top_match["metadata"]["text"],
        requested_amount_usd=40000.0,
        department=top_match["metadata"]["department"],
        soc2_certified=top_match["metadata"]["soc2"],
        gdpr_compliant=top_match["metadata"]["gdpr"],
    )
    assert decision.status == ApprovalStatus.APPROVED
    assert decision.risk_score.risk_level == RiskLevel.LOW

