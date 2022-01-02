from django.urls import path

from keymetrics.financials.views import company_detail_view

app_name = "financials"
urlpatterns = [
    path("<str:ticker>/", view=company_detail_view, name="detail"),
]
