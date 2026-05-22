import sqlite3
import datetime

def setup_database():
    conn = sqlite3.connect("procurement.db")
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            pricing_tier TEXT,
            compliance_status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            start_date DATE,
            end_date DATE,
            total_value REAL,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            amount REAL,
            status TEXT,
            created_at DATE,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        )
    """)

    # Clear existing data for fresh setup
    cursor.execute("DELETE FROM purchase_orders")
    cursor.execute("DELETE FROM contracts")
    cursor.execute("DELETE FROM vendors")

    # Insert Vendors
    vendors = [
        ('TechCorp Inc.', 'SaaS', 'Enterprise', 'Compliant'),
        ('CloudServe', 'Infrastructure', 'Standard', 'Under Review'),
        ('SecurIT', 'Security', 'Enterprise', 'Compliant'),
        ('DataLake Analytics', 'SaaS', 'Basic', 'Non-Compliant')
    ]
    cursor.executemany("INSERT INTO vendors (name, category, pricing_tier, compliance_status) VALUES (?, ?, ?, ?)", vendors)

    # Insert Contracts
    contracts = [
        (1, '2025-01-01', '2026-01-01', 120000.00),
        (2, '2025-03-15', '2026-03-15', 45000.00),
        (3, '2024-11-01', '2025-11-01', 85000.00),
        (4, '2025-06-01', '2026-06-01', 15000.00)
    ]
    cursor.executemany("INSERT INTO contracts (vendor_id, start_date, end_date, total_value) VALUES (?, ?, ?, ?)", contracts)

    # Insert Purchase Orders
    pos = [
        (1, 10000.00, 'Approved', '2025-02-01'),
        (1, 10000.00, 'Approved', '2025-03-01'),
        (2, 3750.00, 'Pending', '2025-04-01'),
        (3, 85000.00, 'Approved', '2024-11-05'),
        (4, 15000.00, 'Rejected', '2025-06-10')
    ]
    cursor.executemany("INSERT INTO purchase_orders (vendor_id, amount, status, created_at) VALUES (?, ?, ?, ?)", pos)

    conn.commit()
    conn.close()
    print("Database setup complete. Mock data inserted into procurement.db")

if __name__ == "__main__":
    setup_database()
