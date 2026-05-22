from mcp.server.fastmcp import FastMCP
import sqlite3
import datetime

# Create a FastMCP server named "Procurement Tools"
mcp = FastMCP("Procurement Tools")

@mcp.tool()
def check_vendor_status(vendor_name: str) -> str:
    """
    Checks the compliance and general status of a vendor in the procurement system.
    Use this when you need to verify if a vendor is compliant before approving a PO.
    """
    conn = sqlite3.connect("procurement.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, pricing_tier, compliance_status FROM vendors WHERE name LIKE ?", (f"%{vendor_name}%",))
    row = cursor.fetchone()
    conn.close()
    if row:
        return f"Vendor ID: {row[0]} | Name: {row[1]} | Category: {row[2]} | Tier: {row[3]} | Compliance: {row[4]}"
    return f"Vendor '{vendor_name}' not found."

@mcp.tool()
def submit_approval_request(vendor_id: int, amount: float) -> str:
    """
    Submits a new purchase order request for a vendor.
    Requires vendor_id and the PO amount. Returns confirmation.
    """
    conn = sqlite3.connect("procurement.db")
    cursor = conn.cursor()
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO purchase_orders (vendor_id, amount, status, created_at) VALUES (?, ?, 'Pending Approval', ?)", 
                   (vendor_id, amount, date_str))
    conn.commit()
    conn.close()
    return f"Approval request for ${amount} to vendor ID {vendor_id} submitted successfully and is pending approval."

@mcp.tool()
def get_recent_pos(limit: int = 5) -> str:
    """
    Gets the most recent purchase orders.
    """
    conn = sqlite3.connect("procurement.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT po.id, v.name, po.amount, po.status, po.created_at 
        FROM purchase_orders po 
        JOIN vendors v ON po.vendor_id = v.id 
        ORDER BY po.id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "No recent purchase orders found."
        
    result = "Recent POs:\n"
    for r in rows:
        result += f"- PO #{r[0]}: {r[1]} - ${r[2]} ({r[3]}) on {r[4]}\n"
    return result

if __name__ == "__main__":
    # Start the FastMCP server (will use stdio by default)
    mcp.run()
