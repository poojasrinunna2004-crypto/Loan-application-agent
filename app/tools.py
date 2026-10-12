import json

from langchain_core.tools import tool

from app import service


@tool
def list_mock_customers() -> str:
    """List fictional customers available in the local training database."""
    return json.dumps(service.list_customers())


@tool
def create_loan_application(
    customer_id: int,
    loan_type: str,
    amount: float,
    term_months: int,
    purpose: str,
) -> str:
    """Create a loan application draft; this tool never submits it."""
    application = service.create_draft(
        customer_id, loan_type, amount, term_months, purpose
    )
    return json.dumps(application)


@tool
def submit_loan_application(application_id: int, confirmation: bool) -> str:
    """Submit a mock draft only when the user explicitly confirms first."""
    application = service.submit_application(application_id, confirmation)
    return json.dumps(application)


loan_application_tools = [
    list_mock_customers,
    create_loan_application,
    submit_loan_application,
]
