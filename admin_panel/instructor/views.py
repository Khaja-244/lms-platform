import os

from django.shortcuts import render


def _context():
    return {"fastapi_base_url": os.environ.get("FASTAPI_BASE_URL", "http://localhost:8001")}


def login_view(request):
    return render(request, "instructor/login.html", _context())


def dashboard_view(request):
    return render(request, "instructor/dashboard.html", _context())
