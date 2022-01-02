from django.db.models import Count  # , OuterRef, Subquery
from django.template.response import TemplateResponse

from keymetrics.financials.models import Company, FinancialFact

# class CompanyDetailView(DetailView):
#
#     model = Company
#     slug_field = "tickers__ticker"
#     slug_url_kwarg = "ticker"
#
#
#
# company_detail_view = CompanyDetailView.as_view()


def company_detail_view(request, ticker: str):
    company = Company.objects.get(tickers__ticker=ticker)
    all_facts = (
        FinancialFact.objects.select_all_related()
        .for_company(company=company)
        .for_period(period="annual")
        .has_alias()
        .order_by("concept__alias__id", "-period__end_date")
    )  # .distinct('concept__alias_id', 'period__end_date')
    # all_facts = FinancialFact.objects.select_all_related().for_company(company=company).
    # for_period(period="year").has_alias().order_by('concept__name', '-period__end_date').
    # distinct('concept__name', 'period__end_date')
    x = (
        FinancialFact.objects.for_company(company=company)
        .for_period("annual")
        .has_alias()
        .values("concept__alias", "period")
        .annotate(a_count=Count("period"))
        .filter(a_count__gt=2)
        .order_by()
    )
    # x = FinancialFact.objects.(Subquery(y))

    context = {"object": company, "facts": all_facts, "x": x}
    return TemplateResponse(request, "financials/company_detail.html", context)
