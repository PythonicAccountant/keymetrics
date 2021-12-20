from django.db import models
from django.utils.translation import gettext_lazy as _


class Company(models.Model):
    name = models.CharField(max_length=255)
    ticker = models.CharField(unique=True, max_length=10)
    CIK = models.IntegerField()
    istracked = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return f"{self.ticker} - {self.name}"

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


class Filing(models.Model):
    TYPE_10Q = "10-Q"
    TYPE_10K = "10-K"
    TYPE_10Q_A = "10-Q/A"
    TYPE_10K_A = "10-K/A"

    TYPE_CHOICES = [
        (TYPE_10Q, "10-Q"),
        (TYPE_10K, "10-K"),
        (TYPE_10Q_A, "10-Q/A"),
        (TYPE_10K_A, "10-K/A"),
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


class FinancialConcept(models.Model):
    TYPE_AS_OF = "ao"
    TYPE_PERIOD_ENDED = "pe"

    TYPE_CHOICES = [
        (TYPE_AS_OF, "As of"),
        (TYPE_PERIOD_ENDED, "Period ended"),
    ]

    tag = models.CharField(_("XBRL Tag"), max_length=255, unique=True)
    name = models.CharField(_("Financial Concept Name"), max_length=255)
    description = models.TextField(_("Concept Description"))
    unit = models.CharField(max_length=50)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.name}"


class TimeDimension(models.Model):
    key = models.CharField(max_length=50, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField()
    months = models.IntegerField(null=True, blank=True)

    def __str__(self):
        if not self.months:
            return f"{self.end_date}"
        else:
            return f"{self.months} months ended {self.end_date}"


class FinancialFact(models.Model):
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

    def __str__(self):
        return f"{self.concept} - {self.period}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "concept", "period", "value"],
                name="unique financial fact",
            )
        ]
