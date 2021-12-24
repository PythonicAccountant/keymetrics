import json
from unittest.mock import Mock, patch

import pytest
import requests
from django.core.management import call_command

import keymetrics.financials.management.commands._call_sec_api as call_api
from keymetrics.financials.management.commands._checksum_checker import checksum_checker
from keymetrics.financials.management.commands.load_companies import save_company_data
from keymetrics.financials.management.commands.load_financial_facts import (
    process_dates,
    save_new_financial_concepts,
    save_new_financial_facts,
    save_new_time_dimensions,
)
from keymetrics.financials.management.commands.update_tracked_companies import (
    reset_tracked_companies,
    update_tracked_companies,
)
from keymetrics.financials.models import (
    Company,
    FinancialConcept,
    FinancialFact,
    Ticker,
    TimeDimension,
)

from .factories import (
    ChecksumFactory,
    CompanyFactory,
    FilingFactory,
    FinancialConceptFactory,
    TickerFactory,
    TimeDimensionFactory,
)

pytestmark = pytest.mark.django_db

test_data = [
    (
        # Input
        {"start": "2020-01-01", "end": "2020-03-31"},
        # Expected
        {
            "start": "2020-01-01",
            "end": "2020-03-31",
            "time_key": "2020-01-012020-03-313",
            "num_months": 3,
        },
    ),
    (
        # Input
        {"start": "2020-03-05", "end": "2020-03-31"},
        # Expected
        {
            "start": "2020-03-05",
            "end": "2020-03-31",
            "time_key": "2020-03-052020-03-311",
            "num_months": 1,
        },
    ),
    (
        # Input
        {"end": "2020-03-31"},
        # Expected
        {
            "start": None,
            "end": "2020-03-31",
            "time_key": "2020-03-31",
            "num_months": None,
        },
    ),
]


@pytest.mark.parametrize("data, expected", test_data)
def test_process_dates(data, expected):
    """Test dates are processed and number of months in period calculated."""
    dates = process_dates(data)
    assert expected == dates


class MockResponse:
    """
    Mock Response object for valid call to SEC API
    """

    @staticmethod
    def json():
        return {"cik": "00000"}

    @property
    def content(self):
        return json.dumps({"cik": "00000"}).encode("UTF-8")

    @staticmethod
    def raise_for_status():
        pass


def test_get_sec_data(monkeypatch):
    """Test successful call to SEC API"""

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    data = call_api.get_sec_data("fakeurl.com")
    assert data["data"] == {"cik": "00000"}


class MockBadResponse:
    """
    Mock Response object for bad response (Error)
    """

    @staticmethod
    def raise_for_status():
        raise requests.exceptions.HTTPError("HTTP Error")


def test_get_sec_data_exception_handling(monkeypatch, caplog):
    """Test error in call to SEC API"""

    def mock_get(*args, **kwargs):
        return MockBadResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    call_api.get_sec_data("fakeurl.com")
    assert "HTTP Error" in caplog.text


@patch("keymetrics.financials.management.commands.load_companies.get_sec_data")
def test_load_companies(mock_sec_get_data):
    """Test Call SEC API and add 1 company and 2 tickers"""
    response_data = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 320193, "ticker": "AAPLFake", "title": "Apple Inc."},
    }

    mock_sec_get_data.return_value = {"data": response_data, "checksum": "checksum"}
    call_command("load_companies")
    companies = Company.objects.all()
    tickers = Ticker.objects.all()
    assert len(companies) == 1
    assert len(tickers) == 2


@patch("keymetrics.financials.management.commands.load_companies.get_sec_data")
@pytest.mark.django_db
def test_companies_null_name_replaced_by_ticker(mock_sec_get_data):
    """Test null company replaced by ticker if title(company name) is blank."""
    response_data = {
        "0": {
            "cik_str": 320193,
            "ticker": "AAPL",
            "title": None,
        },
        "1": {"cik_str": 320193, "ticker": "AAPLFake", "title": "Apple Inc."},
    }

    mock_sec_get_data.return_value = {"data": response_data, "checksum": "checksum"}
    save_company_data()
    null_name_replaced = Company.objects.filter(name="AAPL")
    assert len(null_name_replaced) == 1


class MockFactResponse:
    """
    Mock Response object for valid call to SEC Facts API
    """

    @staticmethod
    def json():
        sample_data = {
            "cik": 1111111,
            "entityName": "Fake.ai",
            "facts": {
                "dei": {
                    "EntityPublicFloat": {
                        "label": "Entity Public Float",
                        "description": "etc etc",
                        "units": {
                            "USD": [
                                {
                                    "end": "2021-04-30",
                                    "val": 4300000000,
                                    "accn": "0001111111-11-011111",
                                    "fy": 2021,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2021-01-01",
                                    "frame": "CY2021Q1I",
                                }
                            ]
                        },
                    }
                },
                "us-gaap": {
                    "AccountsPayableCurrent": {
                        "label": "Accounts Payable, Current",
                        "description": "etc etc",
                        "units": {
                            "USD": [
                                {
                                    "end": "2020-04-30",
                                    "val": 4726000,
                                    "accn": "0001111111-11-111111",
                                    "fy": 2021,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2021-01-01",
                                    "frame": "CY2020Q1I",
                                }
                            ]
                        },
                    }
                },
            },
        }
        return sample_data

    @property
    def content(self):
        return json.dumps({"cik": "00000"}).encode("UTF-8")

    @staticmethod
    def raise_for_status():
        pass


def test_save_new_financial_concepts():
    """Test management command function that adds financial concepts"""
    gaap_data = MockFactResponse.json()["facts"]["us-gaap"]
    save_new_financial_concepts(gaap_data)
    concepts = FinancialConcept.objects.all()
    assert len(concepts) == 1


def test_save_new_financial_concepts_if_doesnt_exist():
    """Test management command function that adds financial concepts only if new."""
    gaap_data = MockFactResponse.json()["facts"]["us-gaap"]
    save_new_financial_concepts(gaap_data)
    save_new_financial_concepts(gaap_data)
    concepts = FinancialConcept.objects.all()
    assert len(concepts) == 1


def test_save_new_time_dimensions():
    """Test management command function that adds new time dimensions"""
    gaap_data = MockFactResponse.json()["facts"]["us-gaap"]
    save_new_time_dimensions(gaap_data)
    time_dimensions = TimeDimension.objects.all()
    assert len(time_dimensions) == 1
    assert time_dimensions[0].key == "2020-04-30"


def test_save_new_time_dimensions_if_doesnt_exist():
    """Test management command function that adds new time dimensions only if new"""
    gaap_data = MockFactResponse.json()["facts"]["us-gaap"]
    save_new_time_dimensions(gaap_data)
    save_new_time_dimensions(gaap_data)
    time_dimensions = TimeDimension.objects.all()
    assert len(time_dimensions) == 1


def test_save_new_financial_facts():
    gaap_data = MockFactResponse.json()["facts"]["us-gaap"]
    company = CompanyFactory(CIK=1111111, name="Fake.ai")
    FilingFactory(company=company, accn_num="0001111111-11-111111")
    FinancialConceptFactory(tag="AccountsPayableCurrent")
    TimeDimensionFactory(key="2020-04-30", end_date="2020-04-30")
    save_new_financial_facts(gaap_data, company)
    facts = FinancialFact.objects.all()
    assert len(facts) == 1


@patch("keymetrics.financials.management.commands.load_financial_facts.get_sec_data")
def test_load_financial_facts_command(mock_sec_get_data: Mock):
    """Test entire financial fact management command (Loads TimeDimensions,
    Financial Concepts as well as FinancialFacts"""
    response_data = MockFactResponse.json()
    company = CompanyFactory(CIK=1111111, name="Fake.ai")
    FilingFactory(company=company, accn_num="0001111111-11-111111")
    mock_sec_get_data.return_value = {"data": response_data, "checksum": "checksum"}
    call_command("load_financial_facts")
    facts = FinancialFact.objects.all()
    assert len(facts) == 1
    assert facts[0].value == 4726000


@patch("keymetrics.financials.management.commands.load_financial_facts.get_sec_data")
def test_load_financial_facts_command_doesnt_add_new_if_checksum_matches(
    mock_sec_get_data: Mock,
):
    """Tests checksum checking logic, no new objects created if checksum matches from beginning"""

    response_data = MockFactResponse.json()
    company = CompanyFactory(CIK=1111111, name="Fake.ai")
    FilingFactory(company=company, accn_num="0001111111-11-111111")
    ChecksumFactory(company=company, api_type="F", checksum="abc123")
    mock_sec_get_data.return_value = {"data": response_data, "checksum": "abc123"}
    call_command("load_financial_facts")
    facts = FinancialFact.objects.all()
    assert len(facts) == 0


def test_reset_tracked_companies(company: Company):
    """Test management command for resetting tracked companies"""
    tracked_companies = Company.objects.filter(istracked=True)
    assert len(tracked_companies) == 1
    reset_tracked_companies()
    tracked_companies = Company.objects.filter(istracked=True)
    assert len(tracked_companies) == 0


def test_update_tracked_companies():
    """Test management command for updating tracked companies"""
    company1 = CompanyFactory(istracked=False)
    company2 = CompanyFactory(istracked=False)
    ticker1 = TickerFactory(company=company1)
    TickerFactory(company=company2)

    tracked_company_list = [ticker1.ticker]
    update_tracked_companies(tracked_company_list)

    tracked_companies = Company.objects.filter(istracked=True)
    assert len(tracked_companies) == 1
    assert tracked_companies[0] == company1


def test_checksum_checker_returns_true_if_match():
    company = CompanyFactory(CIK=1111111, name="Fake.ai")
    FilingFactory(company=company, accn_num="0001111111-11-111111")
    ChecksumFactory(company=company, api_type="F", checksum="abc123")
    current_checksum = "abc123"
    match = checksum_checker(
        current_checksum=current_checksum, company=company, api_type="F"
    )
    assert match is True


def test_checksum_checker_returns_false_if_no_match():
    company = CompanyFactory(CIK=1111111, name="Fake.ai")
    FilingFactory(company=company, accn_num="0001111111-11-111111")
    ChecksumFactory(company=company, api_type="F", checksum="11111")
    current_checksum = "abc123"
    match = checksum_checker(
        current_checksum=current_checksum, company=company, api_type="F"
    )
    assert match is False
