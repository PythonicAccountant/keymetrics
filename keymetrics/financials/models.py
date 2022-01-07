import hashlib
from decimal import Decimal

from django.db import models
from django.db.models import Case, Count, F, OuterRef, Q, Subquery, When
from django.db.models.functions import Cast, ExtractMonth, ExtractYear
from django.utils.translation import gettext_lazy as _


class Company(models.Model):
    name = models.CharField(max_length=255)
    CIK = models.IntegerField(unique=True)
    fiscal_year_end = models.CharField(max_length=10, blank=True, null=True)
    istracked = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return f"{self.name}"

    @property
    def zero_padded_cik(self):
        str_cik = str(self.CIK)
        len_cik = len(str_cik)
        if len_cik < 10:
            zeros = "0" * (10 - len_cik)
            str_cik = zeros + str_cik
        return str_cik

    @property
    def sec_submissions_url(self):
        return f"https://data.sec.gov/submissions/CIK{self.zero_padded_cik}.json"

    @property
    def sec_facts_url(self):
        return (
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.zero_padded_cik}.json"
        )


class TickerManager(models.Manager):
    @property
    def paren_ticker_list(self) -> str:
        return (
            str(list(self.values_list("ticker", flat=True)))
            .replace("[", "(")
            .replace("]", ")")
            .replace("'", "")
        )


class Ticker(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="tickers"
    )
    ticker = models.CharField(max_length=20, unique=True)
    objects = TickerManager()

    def __str__(self):
        return self.ticker


class Filing(models.Model):
    TYPE_10Q = "10-Q"
    TYPE_10K = "10-K"
    TYPE_10Q_A = "10-Q/A"
    TYPE_10K_A = "10-K/A"
    TYPE_8K = "8-K"
    TYPE_8K_A = "8-K/A"

    TYPE_CHOICES = [
        (TYPE_10Q, "10-Q"),
        (TYPE_10K, "10-K"),
        (TYPE_10Q_A, "10-Q/A"),
        (TYPE_10K_A, "10-K/A"),
        (TYPE_8K, "8-K"),
        (TYPE_8K_A, "8-K/A"),
    ]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="filings"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    accn_num = models.CharField(_("Accession Number"), max_length=255, unique=True)
    report_date = models.DateField()
    date_filed = models.DateField()

    def __str__(self):
        return f"{self.company} - {self.type} - {self.report_date}"


class ConceptAlias(models.Model):
    name = models.CharField(_("Alias Name"), max_length=255, unique=True)

    def __str__(self):
        return self.name


class FinancialConcept(models.Model):
    TYPE_AS_OF = "ao"
    TYPE_PERIOD_ENDED = "pe"

    TYPE_CHOICES = [
        (TYPE_AS_OF, "As of"),
        (TYPE_PERIOD_ENDED, "Period ended"),
    ]

    alias = models.ForeignKey(
        ConceptAlias,
        on_delete=models.PROTECT,
        related_name="xbrl_concepts",
        null=True,
        blank=True,
    )
    tag = models.CharField(_("XBRL Tag"), max_length=255, unique=True)
    name = models.CharField(_("Financial Concept Name"), max_length=255)
    description = models.TextField(_("Concept Description"))
    unit = models.CharField(max_length=50)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.name}"


class TimeDimension(models.Model):
    key = models.CharField(max_length=255, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField()
    months = models.IntegerField(null=True, blank=True)

    def __str__(self):
        if not self.months:
            return f"{self.end_date}"
        else:
            return f"{self.months} months ended {self.end_date}"

    @property
    def date_display_str(self) -> str:
        str_date = self.end_date.strftime("%b %Y")
        return str_date

    class Meta:
        ordering = ["-end_date"]


class FactQuerySet(models.QuerySet):
    def select_all_related(self):
        return self.select_related(
            "filing",
            "concept",
            "period",
            "concept__alias",
        )

    def has_alias(self):
        return self.exclude(concept__alias__isnull=True)

    def annual_period(self):
        return self.filter(period__months=12)

    def quarterly_period(self):
        return self.filter(period__months=3)

    def for_period(self, period: str = "annual"):
        """

        :param period: annual or quarter
        :return:
        """
        period_types = ["annual", "quarter"]
        period_dict = {"annual": 12, "quarter": 3}
        type_dict = {
            "annual": FinancialFact.TYPE_ANNUAL,
            "quarter": FinancialFact.TYPE_QUARTER,
        }
        if period not in period_types:
            raise ValueError(f"Invalid period type. Expected one of {period_types}")
        return self.filter(period__months=period_dict[period]).filter(
            type=type_dict[period]
        ) | self.filter(period__months__isnull=True).filter(type=type_dict[period])

    def for_company(self, company: Company):
        return self.filter(company=company)

    def latest_fact(self):
        query = (
            ConceptAlias.objects
            # .filter(xbrl_concepts=OuterRef("concept"))
            .order_by("xbrl_concepts__financial_facts__filing__date_filed").values(
                "xbrl_concepts__financial_facts__filing_id"
            )
        )
        return self.annotate(latest=Subquery(query[:1])).filter(filing_id=F("latest"))

    def add_filing_count(self, company: Company):
        query = (
            FinancialFact.objects.filter(
                Q(concept__alias=OuterRef("concept__alias"))
                & Q(period=OuterRef("period"))
                & Q(company=company)
            )
            .values("concept__alias", "period")
            .order_by()
            .annotate(a_count=Count("*"))
            .values("a_count")[:1]
        )
        return self.annotate(
            filing_count=Subquery(query, output_field=models.IntegerField())
        )

    def is_framed(self):
        return self.filter(is_framed=True)

    def current_year_and_month(self):
        return self.annotate(
            current_year=ExtractYear("period__end_date"),
            last_year=F("current_year") - 1,
            month=ExtractMonth("period__end_date"),
        )

    def get_last_year_value(self):
        query = FinancialFact.objects.filter(
            period__end_date__month=OuterRef("month"),
            period__end_date__year=OuterRef("last_year"),
            concept__alias=OuterRef("concept__alias"),
            company=OuterRef("company"),
        ).values("value")[:1]
        return self.current_year_and_month().annotate(
            py_value=Subquery(query, output_field=models.BigIntegerField())
        )

    def get_yoy_delta(self):
        return self.get_last_year_value().annotate(
            yoy_delta=Case(
                When(py_value__isnull=True, then=0),
                When(py_value__isnull=False, then=(F("value") - F("py_value"))),
                output_field=models.BigIntegerField(),
            )
        )

    def calc_delta_pct(self):
        return self.get_yoy_delta().annotate(
            delta_pct=Case(
                When(yoy_delta__exact=0, then=Decimal(0)),
                When(yoy_delta__exact="none", then=Decimal(0)),
                default=Cast(
                    (F("yoy_delta") / F("py_value")), output_field=models.DecimalField()
                ),
                output_field=models.DecimalField(),
            )
        )

    # def as_amended(self):
    #     If the same financial fact exists under 10-K/A or 10-Q/A then use that (as amended)
    #     :return:
    #     """
    #     # return self.filter(period__months=12)
    #     return self.values('concept', 'period').annotate(count=Count('id'))
    #
    #


class FinancialFact(models.Model):
    """ """

    TYPE_ANNUAL = "a"
    TYPE_QUARTER = "q"

    TYPE_CHOICES = [
        (TYPE_ANNUAL, "Annual"),
        (TYPE_QUARTER, "Quarter"),
    ]

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="financial_facts"
    )
    filing = models.ForeignKey(
        Filing, on_delete=models.CASCADE, related_name="financial_facts"
    )
    concept = models.ForeignKey(
        FinancialConcept, on_delete=models.CASCADE, related_name="financial_facts"
    )
    period = models.ForeignKey(
        TimeDimension, on_delete=models.CASCADE, related_name="financial_facts"
    )
    value = models.BigIntegerField()
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    is_framed = models.BooleanField(default=False)
    objects = FactQuerySet.as_manager()

    def __str__(self):
        return f"{self.company} - {self.concept} - {self.period}"

    @property
    def round_value(self):
        if 1000 <= self.value < 1000000:
            round_value = round(self.value / 1000, 1)
            return f"{round_value:,}K"

        elif 1000000 <= self.value < 1000000000:
            round_value = round(self.value / 1000000, 1)
            return f"{round_value:,}M"

        elif 1000000000 <= self.value < 1000000000000:
            round_value = round(self.value / 1000000000, 1)
            return f"{round_value:,}B"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "concept", "filing", "period", "value"],
                name="unique financial fact",
            )
        ]
        ordering = ["-period__end_date"]


class Checksum(models.Model):
    """
    Model to store the MD5 checksum value of each API call for each Company.
    Using MD5 for speed not used for any security purpose.

    """

    TYPE_SUBMISSIONS = "S"
    TYPE_FACTS = "F"

    TYPE_CHOICES = [
        (TYPE_SUBMISSIONS, "Submission API"),
        (TYPE_FACTS, "Fact API"),
    ]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="checksums"
    )
    api_type = models.CharField(choices=TYPE_CHOICES, max_length=1)
    checksum = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "api_type"],
                name="unique type api per company",
            )
        ]

    def __str__(self):
        return f"{self.company} - {self.get_api_type_display()}"

    @staticmethod
    def generate_md5(data) -> str:
        """
        Generates MD5 checksum given JSON data

        :param data: Raw Content (JSON) from request object
        :return: MD5 checksum string
        """
        return hashlib.md5(data).hexdigest()
