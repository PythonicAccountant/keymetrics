import logging

from dateutil import parser
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from keymetrics.financials.models import (
    Checksum,
    Company,
    Filing,
    FinancialConcept,
    FinancialFact,
    TimeDimension,
)

from ._call_sec_api import get_sec_data
from ._checksum_checker import checksum_checker
from ._measure import measure

logger = logging.getLogger(__name__)


@measure
def fetch_sec_data():
    """
    Queries DB for all tracked Companies and compiles list of URL's to call
    """
    obs = Company.objects.filter(istracked=True)
    url_list = [c.sec_facts_url for c in obs]
    for url in url_list:
        save_new_data(url)


def save_new_data(url: str):
    """
    Checks if SEC API data received is new and if so calls save new data functions

    :param url: SEC API URL
    """
    resp = get_sec_data(url)
    data = resp["data"]
    current_checksum = resp["checksum"]
    gaap_data = data["facts"]["us-gaap"]
    cik = data["cik"]
    company = Company.objects.get(CIK=cik)

    checksum_match = checksum_checker(
        current_checksum=current_checksum, company=company, api_type=Checksum.TYPE_FACTS
    )
    if not checksum_match:
        save_new_financial_concepts(gaap_data)
        save_new_time_dimensions(gaap_data)
        save_new_financial_facts(gaap_data=gaap_data, company=company)


@measure
def save_new_financial_concepts(gaap_data: dict):
    """
    Saves new Financial Concepts if they do not already exist

    :param gaap_data: SEC data from "us-gaap" key
    """
    for key, value in gaap_data.items():
        if not FinancialConcept.objects.filter(tag=key).exists():
            for unit, instance in value["units"].items():
                concept_type = ""
                for entries in instance:
                    if "start" in entries:
                        concept_type = FinancialConcept.TYPE_PERIOD_ENDED
                    else:
                        concept_type = FinancialConcept.TYPE_AS_OF
                concept = FinancialConcept(
                    tag=key,
                    name=value["label"],
                    description=value["description"],
                    unit=unit,
                    type=concept_type,
                )
            try:
                concept.save()
            except IntegrityError:
                concept.name = concept.tag
                concept.description = concept.tag
                concept.save()


@measure
def save_new_time_dimensions(gaap_data: dict):
    """
    Saves new Time Dimensions if they do not already exist

    :param gaap_data: SEC data from "us-gaap" key
    """
    existing_dimensions_objs = TimeDimension.objects.all()
    existing_dimensions_key_list = [t.key for t in existing_dimensions_objs]

    obj_list = []
    for key, value in gaap_data.items():
        for unit, instance in value["units"].items():
            for entries in instance:
                dates = process_dates(entries)
                if dates["time_key"] not in existing_dimensions_key_list:
                    time_dimension = TimeDimension(
                        key=dates["time_key"],
                        start_date=dates["start"],
                        end_date=dates["end"],
                        months=dates["num_months"],
                    )
                    existing_dimensions_key_list.append(key)
                    obj_list.append(time_dimension)
    TimeDimension.objects.bulk_create(obj_list, ignore_conflicts=True)


@measure
def save_new_financial_facts(gaap_data: dict, company: Company):
    """
    Saves new Financial Facts for a given Company

    :param gaap_data: SEC data from "us-gaap" key
    :param company: Company model object the fact relates to
    :return:
    """
    # existing_facts = FinancialFact.objects.select_related("filing").filter(
    #     company=company
    # )
    # existing_filings = [f.filing.accn_num for f in existing_facts]
    filings = Filing.objects.filter(company=company)
    concepts = FinancialConcept.objects.all()
    time_dimensions = TimeDimension.objects.all()

    obj_list = []
    for key, value in gaap_data.items():
        for unit, instance in value["units"].items():
            for entries in instance:
                dates = process_dates(entries)
                filing = filings.get(accn_num=entries["accn"])
                concept = concepts.get(tag=key)
                period = time_dimensions.get(key=dates["time_key"])
                fact_type = get_fact_type(data=entries, dates=dates, company=company)
                framed = get_is_framed(entries)
                obj = FinancialFact(
                    company=company,
                    filing=filing,
                    concept=concept,
                    period=period,
                    type=fact_type,
                    is_framed=framed,
                    value=int(entries["val"]),
                )
                obj_list.append(obj)
    FinancialFact.objects.bulk_create(obj_list, ignore_conflicts=False)


def get_fact_type(data: dict, dates: dict, company: Company) -> str:
    fact_type = None
    fiscal_year_end = int(company.fiscal_year_end)
    end_dt = parser.parse(data["end"])
    end_int = int(end_dt.strftime("%m%d"))

    if dates["num_months"] == 12:
        fact_type = FinancialFact.TYPE_ANNUAL

    elif dates["num_months"] is None:
        if fiscal_year_end - 7 < end_int < fiscal_year_end + 7:
            fact_type = FinancialFact.TYPE_ANNUAL
        else:
            fact_type = FinancialFact.TYPE_QUARTER
    else:
        fact_type = FinancialFact.TYPE_QUARTER

    return fact_type


def get_is_framed(data: dict) -> bool:
    if "frame" in data:
        return True
    else:
        return False


def process_dates(data: dict) -> dict:
    """
    Financial fact data from API always has "end" date. Only has start date if it is for a time
    range. This function also approximately calculates how many months a time range is given the start
    and end dates.

    :param data: Dictionary for an individual financial fact from the API/US-GAAP data
    :return: Dictionary with the dates as well as an appro
    """
    start = None
    num_months = None
    end = data["end"]

    if "start" in data:
        start_dt = parser.parse(data["start"])
        end_dt = parser.parse(data["end"])
        num_months = round(((end_dt - start_dt).days) / 30.4)
        time_key = data["start"] + data["end"] + str(num_months)
        start = data["start"]
    else:
        time_key = end
    return {"start": start, "end": end, "time_key": time_key, "num_months": num_months}


class Command(BaseCommand):
    def handle(self, *args, **options):
        fetch_sec_data()
