from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import activity_service, invoice_service, payment_service

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "/pay/{subscription_id}",
    response_model=schemas.PaymentOut,
)
def make_payment(
    subscription_id: int,
    request: Request,
    payment_status: str = "success",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return payment_service.make_payment(
        subscription_id,
        current_user,
        db,
        payment_status=payment_status,
        ip_address=activity_service.get_client_ip(request),
    )


@router.get(
    "/",
    response_model=list[schemas.PaymentOut],
)
def payment_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return payment_service.payment_history(
        current_user,
        db,
    )


@router.get(
    "/history",
    response_model=list[schemas.PaymentOut],
)
def payment_history_legacy(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return payment_history(db=db, current_user=current_user)


@router.get("/{payment_id}/invoice/")
def download_invoice(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    payment = invoice_service.get_user_payment(db, payment_id, current_user.id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    pdf_bytes = invoice_service.build_invoice_pdf(payment)
    filename = f"{payment.invoice_number or 'invoice'}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
