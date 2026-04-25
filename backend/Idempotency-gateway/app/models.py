from pydantic import BaseModel, Field, field_validator

# What the client sends when making a payment
class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)        # must be a number greater than 0
    currency: str = Field(..., min_length=3, max_length=3)  # e.g. GHS, USD, RWF

    # make sure currency is always uppercase so "ghs" and "GHS" are treated the same
    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


# What the server sends back after processing
class PaymentResponse(BaseModel):
    status: str
    message: str
    transaction_id: str
    amount: float
    currency: str
    processed_at: str


# Shape of error responses so they all look the same
class ErrorResponse(BaseModel):
    error: str
    detail: str
