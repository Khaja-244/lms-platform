"""
payments/views.py

Payment Management
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .invoice import build_invoice_pdf
from .models import Payment


@login_required
def payment_list(request):
    payments = (
        Payment.objects.select_related(
            "subscription",
            "subscription__user",
            "subscription__plan",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "payments/payment_list.html",
        {
            "payments": payments,
        },
    )


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related(
            "subscription",
            "subscription__user",
            "subscription__plan",
        ),
        pk=pk,
    )

    return render(
        request,
        "payments/payment_detail.html",
        {
            "payment": payment,
        },
    )


@login_required
def payment_invoice(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related(
            "subscription",
            "subscription__user",
            "subscription__plan",
        ),
        pk=pk,
    )
    pdf_bytes = build_invoice_pdf(payment)
    filename = f"{payment.invoice_number or 'invoice'}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
