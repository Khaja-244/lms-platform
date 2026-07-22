from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


GST_RATE = Decimal("0.18")


def invoice_totals(payment):
    total = Decimal(payment.amount or 0).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    subscription_fee = (
        total / (Decimal("1.00") + GST_RATE)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    gst = (total - subscription_fee).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return {
        "subscription_fee": subscription_fee,
        "gst": gst,
        "total": total,
    }


def build_invoice_pdf(payment) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    navy = colors.HexColor("#173B8F")
    pale = colors.HexColor("#EAF1FF")
    line = colors.HexColor("#2F4A75")
    text = colors.HexColor("#111827")

    totals = invoice_totals(payment)
    subscription = payment.subscription
    user = subscription.user
    plan = subscription.plan

    def draw_text(
        x,
        y,
        value,
        size=10,
        bold=False,
        color=text,
        align="left",
    ):
        pdf.setFillColor(color)
        pdf.setFont(
            "Helvetica-Bold" if bold else "Helvetica",
            size,
        )

        if align == "center":
            pdf.drawCentredString(x, y, str(value))
        elif align == "right":
            pdf.drawRightString(x, y, str(value))
        else:
            pdf.drawString(x, y, str(value))

    def draw_table(
        x,
        y,
        col_widths,
        row_height,
        rows,
        header=False,
    ):
        current_y = y

        for row_index, row in enumerate(rows):
            current_x = x

            for col_index, value in enumerate(row):
                if row_index == 0 and header:
                    background_color = navy
                elif col_index == 0:
                    background_color = pale
                else:
                    background_color = colors.white

                pdf.setFillColor(background_color)
                pdf.setStrokeColor(line)
                pdf.setLineWidth(0.6)

                pdf.rect(
                    current_x,
                    current_y - row_height,
                    col_widths[col_index],
                    row_height,
                    stroke=1,
                    fill=1,
                )

                draw_text(
                    current_x + 4 * mm,
                    current_y - row_height + 6 * mm,
                    value,
                    9,
                    (row_index == 0 and header) or col_index == 0,
                    colors.white
                    if row_index == 0 and header
                    else text,
                )

                current_x += col_widths[col_index]

            current_y -= row_height

    left = 28 * mm
    right = width - 28 * mm
    y = height - 36 * mm

    # Platform heading
    draw_text(
        width / 2,
        y,
        "Subscription-Based Video Learning Platform",
        16,
        True,
        navy,
        "center",
    )

    y -= 14 * mm

    # Company information
    draw_text(left + 8 * mm, y, "SVLP", 30, True, navy)

    draw_text(
        right,
        y + 8 * mm,
        "Location : Hyderabad, Telangana",
        9,
        False,
        text,
        "right",
    )

    draw_text(
        right,
        y - 3 * mm,
        "Email : support@svlplatform.com",
        9,
        False,
        text,
        "right",
    )

    draw_text(
        right,
        y - 10 * mm,
        "Phone : +91 9876543210",
        9,
        False,
        text,
        "right",
    )

    draw_text(
        right,
        y - 17 * mm,
        "www.svlplatform.com",
        9,
        False,
        text,
        "right",
    )

    # Separator
    y -= 28 * mm
    pdf.setStrokeColor(navy)
    pdf.line(left, y, right, y)

    # Invoice title
    y -= 14 * mm

    draw_text(
        width / 2,
        y,
        "SUBSCRIPTION INVOICE",
        15,
        True,
        navy,
        "center",
    )

    # Invoice information
    y -= 8 * mm

    issue_date = (
        payment.paid_at.strftime("%d %b %Y")
        if payment.paid_at
        else "-"
    )

    status = (
        "Paid"
        if payment.payment_status == "success"
        else payment.get_payment_status_display()
    )

    draw_table(
        left,
        y,
        [32 * mm, 52 * mm, 32 * mm, 47 * mm],
        11 * mm,
        [
            [
                "Invoice No",
                payment.invoice_number or "-",
                "Issue Date",
                issue_date,
            ],
            [
                "Billed To",
                user.name,
                "Payment Status",
                status,
            ],
            [
                "Email",
                user.email,
                "Transaction ID",
                payment.transaction_id or "-",
            ],
        ],
    )

    # Membership details
    y -= 48 * mm
    draw_text(left, y, "Membership Details", 12, True)

    y -= 4 * mm

    draw_table(
        left - 7 * mm,
        y,
        [
            32 * mm,
            32 * mm,
            37 * mm,
            37 * mm,
            35 * mm,
        ],
        11 * mm,
        [
            [
                "Plan",
                "Duration",
                "Start Date",
                "End Date",
                "Amount",
            ],
            [
                plan.name,
                f"{plan.duration_days} Days",
                (
                    subscription.start_date.strftime("%d %b %Y")
                    if subscription.start_date
                    else "-"
                ),
                (
                    subscription.end_date.strftime("%d %b %Y")
                    if subscription.end_date
                    else "-"
                ),
                f"Rs. {totals['subscription_fee']}",
            ],
        ],
        header=True,
    )

    # Payment summary
    y -= 36 * mm
    draw_text(left, y, "Payment Summary", 12, True)

    y -= 4 * mm

    draw_table(
        left + 2 * mm,
        y,
        [102 * mm, 51 * mm],
        10 * mm,
        [
            [
                "Subscription Fee",
                f"Rs. {totals['subscription_fee']}",
            ],
            [
                "GST (18%)",
                f"Rs. {totals['gst']}",
            ],
            [
                "Total Amount",
                f"Rs. {totals['total']}",
            ],
        ],
    )

    # Payment details
    y -= 42 * mm
    draw_text(left, y, "Payment Details", 12, True)

    y -= 4 * mm

    method = (
        payment.get_payment_method_display()
        if payment.payment_method
        else "Credit / Debit Card"
    )

    draw_table(
        left + 2 * mm,
        y,
        [55 * mm, 98 * mm],
        10 * mm,
        [
            ["Payment Method", method],
            [
                "Transaction ID",
                payment.transaction_id or "-",
            ],
            ["Payment Status", status],
            ["Payment Date", issue_date],
        ],
    )

    # Footer - positioned below the Payment Details table
    draw_text(
        width / 2,
        10 * mm,
        "Thank you for your payment and for learning with AKR LMS!",
        9,
        True,
        colors.HexColor("#475569"),
        "center",
    )

    # These lines are required to produce a valid PDF.
    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return buffer.getvalue()