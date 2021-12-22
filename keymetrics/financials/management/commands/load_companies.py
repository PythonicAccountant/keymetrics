from django.core.management.base import BaseCommand

from keymetrics.financials.models import Company, Ticker

from ._call_sec_api import get_sec_data


def save_company_data():
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = get_sec_data(url)
    data = resp["data"]
    objs_list = []
    for key, value in data.items():
        name = value["title"]
        if not name:
            name = value["ticker"]
        obj = Company(
            CIK=int(value["cik_str"]),
            name=name,
        )
        objs_list.append(obj)
    Company.objects.bulk_create(objs_list, ignore_conflicts=True)
    save_ticker_data(data=data)

def save_ticker_data(data):
    companies = Company.objects.all()

    objs_list = []
    for key, value in data.items():
        obj = Ticker(
            company=companies.get(CIK=int(value["cik_str"])),
            ticker=value["ticker"]
        )
        objs_list.append(obj)
    Ticker.objects.bulk_create(objs_list, ignore_conflicts=True)








class Command(BaseCommand):
    def handle(self, *args, **options):
        save_company_data()
