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


@pytest.fixture(autouse=True)
def whitenoise_autorefresh(settings):
    """
    Get rid of whitenoise "No directory at" warning, as it's not helpful when running tests.

    Related:
        - https://github.com/evansd/whitenoise/issues/215
        - https://github.com/evansd/whitenoise/issues/191
        - https://github.com/evansd/whitenoise/commit/4204494d44213f7a51229de8bc224cf6d84c01eb
    """
    settings.WHITENOISE_AUTOREFRESH = True
