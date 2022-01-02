from django.core.management.base import BaseCommand

from keymetrics.financials.models import Checksum, Company, Filing

from ._call_sec_api import get_sec_data
from ._checksum_checker import checksum_checker
from ._measure import measure


def fetch_sec_data():
    """
    Queries DB for all tracked Companies and compiles list of URL's to call
    """
    obs = Company.objects.filter(istracked=True)
    url_list = [c.sec_submissions_url for c in obs]
    for url in url_list:
        save_new_filing(url)


@measure
def save_new_filing(url: str):
    """
    Checks if SEC API data received is new and if so calls process_submissions function

    :param url: SEC API URL
    :return: None
    """
    resp = get_sec_data(url)
    data = resp["data"]
    current_checksum = resp["checksum"]
    cik = data["cik"]
    year_end = data["fiscalYearEnd"]
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
        update_fiscal_year_end(company=company, year_end=year_end)

        # Submissions API only returns most recent 1000 filings, older companies have more in extra submission files
        if extra_files:
            extra_file_list = data["filings"]["files"]
            file_names = [x["name"] for x in extra_file_list]
            for file in file_names:
                url = "https://data.sec.gov/submissions/" + file
                resp = get_sec_data(url)
                data = resp["data"]
                process_submissions(company=company, filing_data=data)


def update_fiscal_year_end(company: Company, year_end: str):
    if company.fiscal_year_end != year_end:
        company.fiscal_year_end = year_end
        company.save()


def process_submissions(company: Company, filing_data: dict):
    """
    Adds all 10-K/10-Q (and amended versions) from the SEC API data

    :param company: Company model object
    :param filing_data:
    :return: None
    """
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
