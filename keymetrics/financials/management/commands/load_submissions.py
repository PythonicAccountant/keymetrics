from django.core.management.base import BaseCommand

from keymetrics.financials.models import Checksum, Company, Filing

from ._call_sec_api import get_sec_data
from ._checksum_checker import checksum_checker
from ._measure import measure


def fetch_sec_data():
    obs = Company.objects.filter(istracked=True)
    url_list = [c.sec_submissions_url for c in obs]
    for url in url_list:
        save_new_filing(url)


@measure
def save_new_filing(url: str):
    resp = get_sec_data(url)
    data = resp["data"]
    current_checksum = resp["checksum"]
    cik = data["cik"]
    company = Company.objects.get(CIK=cik)
    filing_data = data["filings"]["recent"]
    extra_files = False
    if data["filings"]["files"]:
        extra_files = True

    checksum_match = checksum_checker(
        current_checksum=current_checksum,
        company=company,
        api_type=Checksum.TYPE_SUBMISSIONS,
    )
    if not checksum_match:
        process_submissions(company=company, filing_data=filing_data)

        if extra_files:
            extra_file_list = data["filings"]["files"]
            file_names = [x["name"] for x in extra_file_list]
            for file in file_names:
                url = "https://data.sec.gov/submissions/" + file
                resp = get_sec_data(url)
                data = resp["data"]
                process_submissions(company=company, filing_data=data)


def process_submissions(company: Company, filing_data: dict):
    form_list = filing_data["form"]
    report_date_list = filing_data["reportDate"]
    filing_date_list = filing_data["filingDate"]
    accn_list = filing_data["accessionNumber"]
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
