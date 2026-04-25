import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Response
from fastapi.responses import JSONResponse

from app.models import PaymentRequest, PaymentResponse
from app.store import idempotency_store

router = APIRouter()


@router.post("/process-payment", status_code=201)
async def process_payment(
    payment: PaymentRequest,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    # Step 1: Create a fingerprint of the request body
    request_hash = idempotency_store.hash_request(payment.model_dump())

    # Step 2: Lock this key so only one request runs at a time
    # If two identical requests arrive together, the second one waits here
    await idempotency_store.acquire_lock(idempotency_key)

    try:
        existing = idempotency_store.get(idempotency_key)

        if existing is not None:

            # Still processing — this shouldn't happen after the lock, but just in case
            if existing.is_processing:
                raise HTTPException(status_code=503, detail="Request is still being processed. Please retry shortly.")

            # Same key but different body — reject it
            if existing.request_hash != request_hash:
                raise HTTPException(status_code=409, detail="Idempotency key already used for a different request body.")

            # Exact duplicate — return the saved response without processing again
            return JSONResponse(
                content=existing.response_body,
                status_code=existing.status_code,
                headers={"X-Cache-Hit": "true", "X-Idempotency-Key": idempotency_key}
            )

        # New key — mark it as processing before we release the lock
        idempotency_store.mark_processing(idempotency_key, request_hash)

    finally:
        idempotency_store.release_lock(idempotency_key)

    # Step 3: Simulate the payment taking 2 seconds
    await asyncio.sleep(2)

    # Step 4: Build the response
    transaction_id = str(uuid.uuid4())
    processed_at = datetime.now(timezone.utc).isoformat()

    response_body = PaymentResponse(
        status="success",
        message=f"Charged {int(payment.amount) if payment.amount == int(payment.amount) else payment.amount} {payment.currency}",
        transaction_id=transaction_id,
        amount=payment.amount,
        currency=payment.currency,
        processed_at=processed_at,
    ).model_dump()

    # Step 5: Save the result so any future duplicate gets this same response
    idempotency_store.save(
        key=idempotency_key,
        request_hash=request_hash,
        response_body=response_body,
        status_code=201
    )

    return JSONResponse(
        content=response_body,
        status_code=201,
        headers={"X-Idempotency-Key": idempotency_key}
    )


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "idempotency-gateway"}
