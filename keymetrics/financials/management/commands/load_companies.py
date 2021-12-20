import json
import urllib.request

from django.core.management.base import BaseCommand

from keymetrics.financials.models import Company


def fetch_sec_data():
    url = "https://www.sec.gov/files/company_tickers.json"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Danny Arguello postman@keymetrics.cloud")
    r = urllib.request.urlopen(req)
    data = json.load(r)
    objs_list = []
    for key, value in data.items():
        obj = Company(
            CIK=int(value["cik_str"]),
            ticker=value["ticker"],
            name=value["title"],
        )
        objs_list.append(obj)
    Company.objects.bulk_create(objs_list, ignore_conflicts=True)


class Command(BaseCommand):
    def handle(self, *args, **options):
        fetch_sec_data()
