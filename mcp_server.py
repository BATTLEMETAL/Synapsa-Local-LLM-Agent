"""
Synapsa Model Context Protocol (MCP) Server
===========================================
Exposes Synapsa tools (invoice history queries, PL NIP validation, and document auditing)
directly to LLMs using the FastMCP framework.

Requirements:
  pip install mcp

Usage:
  python mcp_server.py
"""

import os
import sys
import json
import re

# Add project root to path for resolving imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("❌ Error: 'mcp' library not found. Please install it using: pip install mcp")
    sys.exit(1)

from synapsa.agents.invoice_history import InvoiceHistory
from api import _rule_based_audit

# Initialize FastMCP server
mcp = FastMCP("Synapsa-Audit-Server")


@mcp.tool()
def query_invoice_history(limit: int = 10) -> str:
    """
    Retrieve the list of recently processed invoices from the Synapsa SQLite database.
    Returns details like invoice numbers, values (net/gross), and dates.
    """
    try:
        db = InvoiceHistory()
        records = db.get_all(limit=limit)
        if not records:
            return "No invoices found in the history database."
        return json.dumps(records, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error querying database: {str(e)}"


@mcp.tool()
def get_invoice_statistics() -> str:
    """
    Calculate and return overall statistics of processed invoices:
    total invoice count, total net amount, total gross amount, and Split Payment (MPP) flag counts.
    """
    try:
        db = InvoiceHistory()
        stats = db.get_stats()
        return json.dumps(stats, indent=2)
    except Exception as e:
        return f"Error retrieving statistics: {str(e)}"


@mcp.tool()
def validate_pl_nip(nip: str) -> str:
    """
    Validate a Polish Tax Identification Number (NIP) checksum.
    Checks digit count and computes the weighted check digit.
    """
    digits = re.sub(r'[^\d]', '', nip)
    if len(digits) != 10:
        return f"NIP {nip} is INVALID: Length is {len(digits)} digits (expected 10)."
    
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(digits[i]) * weights[i] for i in range(9)) % 11
    
    is_valid = (checksum == int(digits[9]))
    return f"NIP {nip} is {'VALID' if is_valid else 'INVALID'} (Checksum digit matches)."


@mcp.tool()
def audit_invoice_file(file_path: str) -> str:
    """
    Run a full compliance audit on a local invoice document file (PDF or image).
    Checks invoice header presence, date formatting, NIP validity, MPP thresholds (15,000 PLN),
    and KSeF readiness.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at path '{file_path}'."
    
    try:
        # Run Synapsa's rule-based audit engine
        result = _rule_based_audit(file_path, os.path.basename(file_path))
        return json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error during document audit: {str(e)}"


if __name__ == "__main__":
    print("🚀 Starting Synapsa FastMCP Server...")
    mcp.run()
