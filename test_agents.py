import pytest
import sqlite3
import os
import json
from unittest.mock import patch, MagicMock
from agents import search_vendor_policies, call_ops_tool

# Test SQLite database creation and schema structure
def test_database_schema(tmp_path):
    db_file = tmp_path / "test_procurement.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create vendors table
    cursor.execute("""
        CREATE TABLE vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            pricing_tier TEXT,
            compliance_status TEXT
        )
    """)
    
    # Create contracts table
    cursor.execute("""
        CREATE TABLE contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            start_date DATE,
            end_date DATE,
            total_value REAL,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        )
    """)

    # Insert test data
    cursor.execute("INSERT INTO vendors (name, category, pricing_tier, compliance_status) VALUES (?, ?, ?, ?)",
                   ('Test Vendor', 'SaaS', 'Standard', 'Compliant'))
    vendor_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO contracts (vendor_id, start_date, end_date, total_value) VALUES (?, ?, ?, ?)",
                   (vendor_id, '2025-01-01', '2026-01-01', 5000.00))
    
    conn.commit()

    # Query and assert
    cursor.execute("SELECT name FROM vendors WHERE id = ?", (vendor_id,))
    vendor_name = cursor.fetchone()[0]
    assert vendor_name == "Test Vendor"

    cursor.execute("SELECT total_value FROM contracts WHERE vendor_id = ?", (vendor_id,))
    contract_val = cursor.fetchone()[0]
    assert contract_val == 5000.00

    conn.close()

# Test search_vendor_policies tool when collection is None (fallback state)
def test_search_vendor_policies_db_not_initialized():
    with patch('agents.collection', None):
        response = search_vendor_policies.invoke({"query": "compliance"})
        assert response == "Vector database not initialized."

# Test search_vendor_policies tool with mock documents
def test_search_vendor_policies_success():
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        'documents': [['SLA uptime is 99.9%', 'Data encryption at rest is AES-256']]
    }
    with patch('agents.collection', mock_collection):
        response = search_vendor_policies.invoke({"query": "SLA"})
        assert "SLA uptime is 99.9%" in response
        assert "AES-256" in response
        mock_collection.query.assert_called_once_with(query_texts=["SLA"], n_results=3)

# Test call_ops_tool successfully invoking a mock gateway endpoint
@patch('requests.post')
def test_call_ops_tool_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success-action"}
    mock_post.return_value = mock_response

    args = json.dumps({"param": "val"})
    result = call_ops_tool.invoke({
        "server_name": "devops",
        "tool_name": "restart_service",
        "arguments": args
    })

    assert result == "success-action"
    mock_post.assert_called_once_with(
        "http://localhost:8080/devops/call/restart_service",
        json={"param": "val"},
        timeout=30
    )

# Test call_ops_tool handling network exception failures
@patch('requests.post')
def test_call_ops_tool_failure(mock_post):
    mock_post.side_effect = Exception("Connection refused")

    result = call_ops_tool.invoke({
        "server_name": "devops",
        "tool_name": "restart_service",
        "arguments": "{}"
    })

    assert "Error calling ops tool: Connection refused" in result
