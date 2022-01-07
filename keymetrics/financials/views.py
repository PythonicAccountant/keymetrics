# import pandas as pd
# from django.db.models import Count  # , OuterRef, Subquery
from django.template.response import TemplateResponse

from keymetrics.financials.models import Company, FinancialFact

# def company_detail_view(request, ticker: str):
#     company = Company.objects.get(tickers__ticker=ticker)
#     all_facts = (
#         FinancialFact.objects.select_all_related()
#         .for_company(company=company)
#         .for_period(period="annual")
#         .has_alias()
#         .is_framed()
#         .order_by("concept__alias__id", "-period__end_date", "-filing__date_filed")
#         .distinct('concept__alias_id', 'period__end_date'))
#         # .values('concept__alias__name', 'period__end_date', 'value')
#
#     # df = pd.DataFrame(all_facts)
#     # df = df.pivot(index="concept__alias__name", columns="period__end_date", values="value")
#     # df = df.reset_index()
#     # df_h = df.to_html(index=False)
#
#
#     context = {"object": company, "facts": all_facts}#, "df_h": df_h}
#     return TemplateResponse(request, "financials/company_detail.html", context)


def company_detail_view(request, ticker: str):
    company = Company.objects.get(tickers__ticker=ticker)
    all_facts = (
        FinancialFact.objects.select_all_related()
        .for_company(company=company)
        .for_period(period="annual")
        .has_alias()
        .is_framed()
        .get_yoy_delta()
        .calc_delta_pct()
        .order_by("concept__alias__id", "-period__end_date", "-filing__date_filed")
        .distinct("concept__alias_id", "period__end_date")
    )
    # .values('concept__alias__name', 'period__end_date', 'value')

    # df = pd.DataFrame(all_facts)
    # df = df.pivot(index="concept__alias__name", columns="period__end_date", values="value")
    # df = df.reset_index()
    # df_h = df.to_html(index=False)

    context = {"object": company, "facts": all_facts}  # , "df_h": df_h}
    return TemplateResponse(request, "financials/company_detail.html", context)
