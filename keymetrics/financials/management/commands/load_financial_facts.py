import json
import urllib.request

from dateutil import parser
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from keymetrics.financials.models import (
    Company,
    Filing,
    FinancialConcept,
    FinancialFact,
    TimeDimension,
)


def fetch_sec_data():
    obs = Company.objects.filter(istracked=True)
    url_list = [c.sec_facts_url for c in obs]
    for url in url_list:
        save_new_data(url)


def save_new_data(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Danny Arguello postman@keymetrics.cloud")
    r = urllib.request.urlopen(req)
    data = json.load(r)
    gaap_data = data["facts"]["us-gaap"]
    cik = data["cik"]
    save_new_financial_concepts(gaap_data)
    save_new_time_dimensions(gaap_data)
    save_new_financial_facts(gaap_data=gaap_data, cik=cik)


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


def save_new_time_dimensions(gaap_data):
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
                if not TimeDimension.objects.filter(key=key).exists():
                    time_dimension = TimeDimension(
                        key=key,
                        start_date=start,
                        end_date=end,
                        months=num_months,
                    )
                    time_dimension.save()


def save_new_financial_facts(gaap_data, cik):
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
                filing = Filing.objects.get(accn_num=entries["accn"])
                company = Company.objects.get(CIK=cik)
                concept = FinancialConcept.objects.get(tag=key)
                period = TimeDimension.objects.get(key=time_key)
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
