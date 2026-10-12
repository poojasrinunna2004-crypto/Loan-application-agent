from typing import Any

from app import database


def list_customers() -> list[dict[str, Any]]:
    with database.get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, email, annual_income FROM customers ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def create_draft(
    customer_id: int,
    loan_type: str,
    amount: float,
    term_months: int,
    purpose: str,
) -> dict[str, Any]:
    with database.get_connection() as connection:
        customer = connection.execute(
            "SELECT id FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        if customer is None:
            raise ValueError("Customer was not found in the mock database.")
        cursor = connection.execute(
            """INSERT INTO applications
               (customer_id, loan_type, amount, term_months, purpose)
               VALUES (?, ?, ?, ?, ?)""",
            (customer_id, loan_type, amount, term_months, purpose),
        )
        application_id = cursor.lastrowid
    return get_application(application_id)


def get_application(application_id: int) -> dict[str, Any]:
    with database.get_connection() as connection:
        row = connection.execute(
            """SELECT a.*, c.name AS customer_name, c.email AS customer_email
               FROM applications a JOIN customers c ON c.id = a.customer_id
               WHERE a.id = ?""",
            (application_id,),
        ).fetchone()
    if row is None:
        raise ValueError("Application was not found.")
    return dict(row)


def submit_application(application_id: int, confirmation: bool) -> dict[str, Any]:
    if confirmation is not True:
        raise ValueError("Explicit confirmation is required before submission.")
    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT status FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Application was not found.")
        if row["status"] == "draft":
            connection.execute(
                """UPDATE applications
                   SET status = 'submitted', submitted_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (application_id,),
            )
    return get_application(application_id)
