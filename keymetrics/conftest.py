import pytest

from keymetrics.financials.tests.factories import (
    CompanyFactory,
    FilingFactory,
    FinancialConcept,
    TickerFactory,
)
from keymetrics.users.models import User
from keymetrics.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> User:
    return UserFactory()


@pytest.fixture
def company():
    return CompanyFactory()


@pytest.fixture
def ticker():
    return TickerFactory()


@pytest.fixture
def financialconcept():
    return FinancialConcept()


@pytest.fixture
def filing():
    return FilingFactory()


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.delattr("requests.sessions.Session.request")
