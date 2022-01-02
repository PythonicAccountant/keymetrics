import pytest
from django.urls import resolve, reverse

from keymetrics.financials.models import Ticker

# from keymetrics.users.models import User

pytestmark = pytest.mark.django_db


def test_detail(ticker: Ticker):
    assert (
        reverse("financials:detail", kwargs={"ticker": ticker.ticker})
        == f"/companies/{ticker.ticker}/"
    )
    assert resolve(f"/companies/{ticker.ticker}/").view_name == "financials:detail"
