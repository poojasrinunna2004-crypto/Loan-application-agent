from enum import Enum

from pydantic import BaseModel, Field, StrictBool


class LoanType(str, Enum):
    personal = "personal"
    auto = "auto"
    home = "home"
    business = "business"


class ApplicationDraft(BaseModel):
    customer_id: int = Field(gt=0)
    loan_type: LoanType
    amount: float = Field(gt=0, le=2_000_000)
    term_months: int = Field(gt=0, le=480)
    purpose: str = Field(min_length=5, max_length=500)


class SubmissionConfirmation(BaseModel):
    confirmation: StrictBool
