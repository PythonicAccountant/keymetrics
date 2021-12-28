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
    obs = Company.objects.filter(istracked=True)
    url_list = [c.sec_facts_url for c in obs]
    for url in url_list:
        save_new_data(url)


def save_new_data(url: str):
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
    existing_facts = FinancialFact.objects.select_related("filing").filter(
        company=company
    )
    existing_filings = [f.filing.accn_num for f in existing_facts]
    filings = Filing.objects.filter(company=company)
    concepts = FinancialConcept.objects.all()
    time_dimensions = TimeDimension.objects.all()

    obj_list = []
    for key, value in gaap_data.items():
        for unit, instance in value["units"].items():
            for entries in instance:
                dates = process_dates(entries)
                if entries["form"] not in ["8-K", "8-K/A"]:
                    try:
                        filing = filings.get(accn_num=entries["accn"])
                    except Filing.DoesNotExist as e:
                        print(entries["accn"])
                        logger.error(f'Accn {entries["accn"]} does not exist {e}')
                    concept = concepts.get(tag=key)
                    period = time_dimensions.get(key=dates["time_key"])
                    if entries["accn"] not in existing_filings:
                        obj = FinancialFact(
                            company=company,
                            filing=filing,
                            concept=concept,
                            period=period,
                            value=int(entries["val"]),
                        )
                        obj_list.append(obj)
    FinancialFact.objects.bulk_create(obj_list, ignore_conflicts=True)


def process_dates(data: dict) -> dict:
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
