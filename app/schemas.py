from enum import Enum

from pydantic import BaseModel, Field, StrictBool


class LoanType(str, Enum):
    personal = "personal"
    auto = "auto"
    home = "home"
    business = "business"


class ApplicationDraft(BaseModel):
    customer_id: int = Field(
        gt=0,
        description="ID of a fictional customer from GET /customers.",
        examples=[1],
    )
    loan_type: LoanType = Field(description="Choose personal, auto, home, or business.")
    amount: float = Field(
        gt=0,
        le=2_000_000,
        description="Requested amount in USD. Must be greater than 0 and no more than 2,000,000.",
        examples=[12000],
    )
    term_months: int = Field(
        gt=0,
        le=480,
        description="Repayment period in whole months, from 1 to 480.",
        examples=[36],
    )
    purpose: str = Field(
        min_length=5,
        max_length=500,
        description="Short explanation of the loan purpose (5 to 500 characters).",
        examples=["Home repairs"],
    )


class SubmissionConfirmation(BaseModel):
    confirmation: StrictBool = Field(
        description="Must be the JSON boolean true after the user explicitly confirms."
    )
