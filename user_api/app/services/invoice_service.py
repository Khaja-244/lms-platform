
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from sqlalchemy.orm import Session

from .. import models

GST_RATE = Decimal("0.18")


def invoice_totals(payment: models.Payment) -> dict:
    total = Decimal(payment.amount or 0).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    subscription_fee = (
        total / (Decimal("1.00") + GST_RATE)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    gst = (total - subscription_fee).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return {
        "subscription_fee": subscription_fee,
        "gst": gst,
        "total": total,
    }


def _heading(text, style):
    return Paragraph(f"<b>{text}</b>", style)


def build_invoice_pdf(payment: models.Payment) -> bytes:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title = styles["Heading1"]
    title.alignment = TA_CENTER
    title.textColor = colors.HexColor("#173B8F")

    h2 = styles["Heading2"]
    h2.textColor = colors.HexColor("#173B8F")

    normal = styles["BodyText"]

    story = []

    totals = invoice_totals(payment)
    subscription = payment.subscription
    user = subscription.user
    plan = subscription.plan

    issue_date = payment.paid_at.strftime("%d %b %Y") if payment.paid_at else "-"
    status = "PAID" if payment.payment_status == "success" else (
        payment.payment_status or "-"
    ).upper()

    story.append(_heading("AKR LMS", title))
    story.append(Paragraph("Subscription-Based Video Learning Platform", normal))
    story.append(Paragraph("Hyderabad, Telangana, India", normal))
    story.append(Spacer(1, 10))
    story.append(_heading("TAX INVOICE", h2))
    story.append(Spacer(1, 10))

    info = Table([
        ["Invoice No", payment.invoice_number or "-"],
        ["Invoice Date", issue_date],
        ["Transaction ID", payment.transaction_id or "-"],
        ["Status", status],
    ], colWidths=[120, 260])
    info.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#173B8F")),
        ("TEXTCOLOR", (0,0), (0,-1), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(info)
    story.append(Spacer(1, 14))

    story.append(_heading("Billing Information", h2))
    billing = Table([
        ["Bill From", "Bill To"],
        [
            "AKR LMS\nHyderabad\nsupport@svlplatform.com",
            f"{user.name}\n{user.email}"
        ]
    ], colWidths=[190,190])
    billing.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EAF1FF")),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(billing)
    story.append(Spacer(1, 14))

    story.append(_heading("Subscription Details", h2))
    sub = Table([
        ["Plan","Duration","Start","End","Amount"],
        [
            plan.name,
            f"{plan.duration_days} Days",
            subscription.start_date.strftime("%d %b %Y") if subscription.start_date else "-",
            subscription.end_date.strftime("%d %b %Y") if subscription.end_date else "-",
            f"Rs. {totals['subscription_fee']}",
        ]
    ], colWidths=[70,70,90,90,80])
    sub.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#173B8F")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
    ]))
    story.append(sub)
    story.append(Spacer(1, 14))

    story.append(_heading("Payment Summary", h2))
    summary = Table([
        ["Subscription Fee", f"Rs. {totals['subscription_fee']}"],
        ["GST (18%)", f"Rs. {totals['gst']}"],
        ["Grand Total", f"Rs. {totals['total']}"],
    ], colWidths=[250,150])
    summary.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("BACKGROUND",(0,2),(-1,2),colors.HexColor("#D9F7D9")),
        ("FONTNAME",(0,2),(-1,2),"Helvetica-Bold"),
    ]))
    story.append(summary)
    story.append(Spacer(1, 14))

    story.append(_heading("Payment Details", h2))
    details = Table([
        ["Payment Method", (payment.payment_method or "Card").replace("_"," ").title()],
        ["Payment Status", status],
        ["Payment Date", issue_date],
        ["Transaction ID", payment.transaction_id or "-"],
    ], colWidths=[150,250])
    details.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#F4F4F4")),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
    ]))
    story.append(details)
    story.append(Spacer(1,20))
    story.append(Paragraph(
        "<font color='#666666'>Thank you for choosing AKR LMS.<br/>"
        "support@svlplatform.com | www.svlplatform.com<br/>"
        "This is a computer-generated invoice.</font>",
        normal
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def get_user_payment(db: Session, payment_id: int, user_id: int):
    return (
        db.query(models.Payment)
        .join(models.Subscription)
        .filter(
            models.Payment.id == payment_id,
            models.Subscription.user_id == user_id,
        )
        .first()
    )
