import json
import urllib.request

from django.core.management.base import BaseCommand

from keymetrics.financials.models import Company, Filing


def fetch_sec_data():
    obs = Company.objects.filter(istracked=True)
    url_list = [c.sec_submissions_url for c in obs]
    for url in url_list:
        save_new_filing(url)


def save_new_filing(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Danny Arguello postman@keymetrics.cloud")
    r = urllib.request.urlopen(req)
    data = json.load(r)
    cik = data["cik"]
    company = Company.objects.get(CIK=cik)
    form_list = data["filings"]["recent"]["form"]
    report_date_list = data["filings"]["recent"]["reportDate"]
    filing_date_list = data["filings"]["recent"]["filingDate"]
    accn_list = data["filings"]["recent"]["accessionNumber"]
    indices = [
        i for i, x in enumerate(form_list) if x in ["10-K", "10-Q", "10-K/A", "10-Q/A"]
    ]
    obj_list = []
    for index in indices:
        obj = Filing(
            company=company,
            type=form_list[index],
            accn_num=accn_list[index],
            report_date=report_date_list[index],
            date_filed=filing_date_list[index],
        )
        obj_list.append(obj)
    Filing.objects.bulk_create(obj_list, ignore_conflicts=True)


class Command(BaseCommand):
    def handle(self, *args, **options):
        fetch_sec_data()
