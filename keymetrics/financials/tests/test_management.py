import json
from unittest.mock import patch

import pytest
import requests
from django.core.management import call_command

import keymetrics.financials.management.commands._call_sec_api as call_api
from keymetrics.financials.management.commands.load_companies import save_company_data
from keymetrics.financials.management.commands.load_financial_facts import process_dates
from keymetrics.financials.models import Company, Ticker

test_data = [
    (
        {"start": "2020-01-01", "end": "2020-03-31"},
        {
            "start": "2020-01-01",
            "end": "2020-03-31",
            "time_key": "2020-01-012020-03-313",
            "num_months": 3,
        },
    ),
    (
        {"start": "2020-03-05", "end": "2020-03-31"},
        {
            "start": "2020-03-05",
            "end": "2020-03-31",
            "time_key": "2020-03-052020-03-311",
            "num_months": 1,
        },
    ),
]


@pytest.mark.parametrize("test_data, expected", test_data)
def test_process_dates(test_data, expected):
    dates = process_dates(test_data)
    assert expected == dates


class MockResponse:
    @staticmethod
    def json():
        return {"cik": "00000"}

    @property
    def content(self):
        return json.dumps({"cik": "00000"}).encode("UTF-8")


def test_get_sec_data(monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    data = call_api.get_sec_data("fakeurl.com")
    assert data["data"] == {"cik": "00000"}


@patch("keymetrics.financials.management.commands.load_companies.get_sec_data")
@pytest.mark.django_db
def test_load_companies(mock_sec_get_data):
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
