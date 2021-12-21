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
from ._measure import measure


@measure
def fetch_sec_data():
    obs = Company.objects.filter(istracked=True)
    url_list = [c.sec_facts_url for c in obs]
    for url in url_list:
        save_new_data(url)


def save_new_data(url):
    resp = get_sec_data(url)
    data = resp["data"]
    new_checksum = resp["checksum"]
    gaap_data = data["facts"]["us-gaap"]
    cik = data["cik"]
    company = Company.objects.get(CIK=cik)
    try:
        stored_checksum = Checksum.objects.get(
            company=company, api_type=Checksum.TYPE_FACTS
        )
        stored_checksum = stored_checksum.checksum
    except Checksum.DoesNotExist:
        stored_checksum = None
    if new_checksum != stored_checksum:
        save_new_financial_concepts(gaap_data)
        save_new_time_dimensions(gaap_data)
        save_new_financial_facts(gaap_data=gaap_data, company=company)
        Checksum.objects.update_or_create(
            company=company,
            api_type=Checksum.TYPE_FACTS,
            defaults={"checksum": new_checksum},
        )


@measure
def save_new_financial_concepts(gaap_data):
    for key, value in gaap_data.items():
        if not FinancialConcept.objects.filter(tag=key).exists():
            for unit, instance in value["units"].items():
                concept_type = None
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
def save_new_time_dimensions(gaap_data):
    existing_dimensions = TimeDimension.objects.all()
    existing_dimensions = [t.key for t in existing_dimensions]

    obj_list = []
    for key, value in gaap_data.items():
        for unit, instance in value["units"].items():
            for entries in instance:
                num_months = None
                if "start" in entries:
                    start = parser.parse(entries["start"])
                    end = parser.parse(entries["end"])
                    num_months = (
                        (end.year - start.year) * 12 + (end.month - start.month) + 1
                    )
                    key = entries["start"] + entries["end"] + str(num_months)
                else:
                    start = None
                    end = parser.parse(entries["end"])
                    key = entries["end"]
                if key not in existing_dimensions:
                    time_dimension = TimeDimension(
                        key=key,
                        start_date=start,
                        end_date=end,
                        months=num_months,
                    )
                    existing_dimensions.append(key)
                    obj_list.append(time_dimension)
    TimeDimension.objects.bulk_create(obj_list, ignore_conflicts=True)


@measure
def save_new_financial_facts(gaap_data, company):
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
                if "start" in entries:
                    start = parser.parse(entries["start"])
                    end = parser.parse(entries["end"])
                    num_months = (
                        (end.year - start.year) * 12 + (end.month - start.month) + 1
                    )
                    time_key = entries["start"] + entries["end"] + str(num_months)
                else:
                    start = None
                    end = parser.parse(entries["end"])
                    time_key = entries["end"]
                filing = filings.get(accn_num=entries["accn"])
                concept = concepts.get(tag=key)
                period = time_dimensions.get(key=time_key)
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


class Command(BaseCommand):
    def handle(self, *args, **options):
        fetch_sec_data()
