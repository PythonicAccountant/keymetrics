from django.urls import path

from keymetrics.financials.views import (
    company_detail_view,
    company_list_view,
    filing_list_view,
)

app_name = "financials"
urlpatterns = [
    path("", view=company_list_view, name="list"),
    path("ticker/<str:ticker>/", view=company_detail_view, name="detail"),
    path("filings/", view=filing_list_view, name="filings"),
]
