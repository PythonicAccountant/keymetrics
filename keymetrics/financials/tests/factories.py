from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from keymetrics.financials.models import (
    Company,
    Filing,
    FinancialConcept,
    FinancialFact,
    Ticker,
    TimeDimension,
)


class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company

    name = Faker("company")
    CIK = Faker("pyint", min_value=1, max_value=100000)
    istracked = True


class TickerFactory(DjangoModelFactory):
    class Meta:
        model = Ticker

    company = SubFactory(CompanyFactory)
    ticker = Faker("first_name")


class FilingFactory(DjangoModelFactory):
    class Meta:
        model = Filing

    company = SubFactory(CompanyFactory)
    type = Faker(
        "random_choices", elements=["10-K", "10-Q", "10-K/A", "10-Q/A"], length=1
    )
    accn_num = Faker("phone_number")
    report_date = Faker("date")
    date_filed = Faker("date")


class FinancialConceptFactory(DjangoModelFactory):
    class Meta:
        model = FinancialConcept

    tag = Faker("job")
    name = Faker("job")
    description = Faker("job")
    unit = Faker("job")
    type = Faker(
        "random_choices",
        elements=[FinancialConcept.TYPE_AS_OF, FinancialConcept.TYPE_PERIOD_ENDED],
        length=1,
    )

    def __str__(self):
        return f"{self.name}"


class TimeDimensionFactory(DjangoModelFactory):
    class Meta:
        model = TimeDimension

    key = str(Faker("date"))
    start_date = Faker("date")
    end_date = Faker("date")
    months = Faker("pyint", min_value=1, max_value=100)


class FinancialFactFactory(DjangoModelFactory):
    class Meta:
        model = FinancialFact

    company = SubFactory(CompanyFactory)
    filing = SubFactory(FilingFactory)
    concept = SubFactory(FinancialConceptFactory)
    period = SubFactory(TimeDimensionFactory)
    value = Faker("pyint", min_value=1, max_value=10000000)
