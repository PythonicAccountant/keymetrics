# import pandas as pd
# from django.db.models import Count  # , OuterRef, Subquery
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.template.response import TemplateResponse

from keymetrics.financials.models import Company, Filing, FinancialFact


def company_list_view(request):
    page_obj, page_range, search = _search_companies(request)
    context = {"page_obj": page_obj, "search": search, "page_range": page_range}
    if not request.META.get("HTTP_HX_REQUEST"):
        return TemplateResponse(request, "financials/company_list.html", context)
    else:
        return TemplateResponse(
            request, "financials/company_search_results.html", context
        )


def _search_companies(request):
    search = request.GET.get("search")
    page_number = request.GET.get("page")
    companies = Company.objects.all().order_by("name")

    if search:
        companies = companies.company_search(search)

    paginator = Paginator(companies, 8)
    try:
        page_obj = paginator.page(page_number)
        page_range = paginator.get_elided_page_range(
            number=page_number, on_each_side=1, on_ends=1
        )
    except PageNotAnInteger:
        page_obj = paginator.page(1)
        page_range = paginator.get_elided_page_range(
            number=1, on_each_side=1, on_ends=1
        )

    except EmptyPage:
        page_obj - paginator.page(paginator.num_pages)

    return page_obj, page_range, search or ""


def company_detail_view(request, ticker: str):
    company = Company.objects.get(tickers__ticker=ticker)
    facts = FinancialFact.objects.annual_data_with_yoy_delta().for_company(company)
    context = {"object": company, "facts": facts}
    return TemplateResponse(request, "financials/company_detail.html", context)


def filing_list_view(request):
    filing_list = (
        Filing.objects.all()
        .select_related("company")
        .order_by("-date_filed")
        .annotate(fact_count=Count("financial_facts"))
    )
    paginator = Paginator(filing_list, 10)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj}
    return TemplateResponse(request, "financials/filing_list.html", context)
