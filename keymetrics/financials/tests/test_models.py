import pytest

from .factories import CompanyFactory, FinancialFactFactory

pytestmark = pytest.mark.django_db

test_data = [(1, "0000000001"), (12345, "0000012345"), (12345678, "0012345678")]


@pytest.mark.parametrize("cik, expected", test_data)
def test_company_zero_padded_cik(cik, expected):
    company = CompanyFactory(CIK=cik, name="test")
    assert company.zero_padded_cik == expected


def test_company_get_sec_urls(company):
    assert (
        company.sec_submissions_url
        == f"https://data.sec.gov/submissions/CIK{company.zero_padded_cik}.json"
    )
    assert (
        company.sec_facts_url
        == f"https://data.sec.gov/api/xbrl/companyfacts/CIK{company.zero_padded_cik}.json"
    )


def test_company_str(company):
    assert str(company) == company.name + " ()"


def test_filing_str(filing):
    assert str(filing) == f"{filing.company} - {filing.type} - {filing.report_date}"


def test_ticker_str(ticker):
    assert str(ticker) == ticker.ticker


def test_financial_concept_str(financialconcept):
    assert str(financialconcept) == financialconcept.name


def test_financial_fact_str():
    fact = FinancialFactFactory()
    assert str(fact) == f"{fact.company} - {fact.concept} - {fact.period}"
