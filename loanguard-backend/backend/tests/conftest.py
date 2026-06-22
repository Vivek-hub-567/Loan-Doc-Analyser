"""
backend/tests/conftest.py — Shared pytest fixtures for LoanGuard AI backend tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add project root to path
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

SAMPLE_LOAN_TEXT = """
This Loan Agreement ("Agreement") is entered into between FastCash Digital Finance Pvt. Ltd. ("Lender")
and the borrower identified in the application ("Borrower") on the date of digital acceptance.

The Lender hereby agrees to provide a personal loan of ₹10,000 (Rupees Ten Thousand Only) subject to the
following terms and conditions:

1. LOAN AMOUNT AND DISBURSEMENT
The sanctioned loan amount is ₹10,000. However, a processing fee of 25% amounting to ₹2,500 will be
deducted upfront before disbursement. Additionally, GST extra will be charged on all applicable fees.
Insurance bundled with the loan is mandatory and non-refundable. The net amount disbursed to the borrower
shall be approximately ₹7,300 after all upfront deductions.

2. INTEREST RATE AND EMI
The interest rate is 36% per annum. The EMI of ₹4,707 is payable on the 5th of every month for 12 months.
Penal interest of 3% per month will be charged on any overdue EMI amount. Late payment fee of ₹500 per
day will be applied for each day of delay beyond the due date.

3. DEFAULT AND RECOVERY
In case of default, the Lender may, at its sole discretion and without notice, accelerate the entire
outstanding loan balance making it immediately due and payable. The Lender reserves the right to appoint
a recovery agent and initiate SARFAESI proceedings. Asset seizure may be carried out without prior notice
to the Borrower. The Borrower shall be liable for all recovery costs.

4. BORROWER CONSENT
The Borrower irrevocably authorises the Lender to access SMS, contact list, location, and device data
for the purposes of credit assessment and collection. Behavior monitoring and usage monitoring of the
app shall be permitted at all times. The Lender may share this data with third parties without further
consent as per our privacy policy.

5. LENDER'S DISCRETION
The Lender, at its absolute discretion, may modify any term of this Agreement at any time and without
prior notice to the Borrower. The Borrower irrevocably waives the right to challenge such modifications.
"""

SHORT_TEXT = "This is a short loan document."


@pytest.fixture(scope="session")
def sample_text() -> str:
    return SAMPLE_LOAN_TEXT


@pytest.fixture(scope="session")
def short_text() -> str:
    return SHORT_TEXT


@pytest.fixture(scope="session")
def test_client():
    from backend.main import app
    with TestClient(app) as client:
        yield client
