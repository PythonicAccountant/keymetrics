from django.core.management.base import BaseCommand

from keymetrics.financials.models import Company

from ._call_sec_api import get_sec_data


def save_company_ticker_data():
    url = "https://www.sec.gov/files/company_tickers.json"
    data = get_sec_data(url)
    objs_list = []
    for key, value in data.items():
        name = value["title"]
        if not name:
            name = value["ticker"]
        obj = Company(
            CIK=int(value["cik_str"]),
            ticker=value["ticker"],
            name=name,
        )
        objs_list.append(obj)
    Company.objects.bulk_create(objs_list, ignore_conflicts=True)


class Command(BaseCommand):
    def handle(self, *args, **options):
        save_company_ticker_data()
