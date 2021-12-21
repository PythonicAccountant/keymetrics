import requests
from pyrate_limiter import Duration, Limiter, RequestRate

from config.settings.base import env
from keymetrics.financials.models import Checksum

limiter = Limiter(RequestRate(10, Duration.SECOND))


@limiter.ratelimit("SEC", delay=True)
def get_sec_data(url: str):
    headers = {"User-Agent": env("SEC_API_USER_AGENT")}
    r = requests.get(url, headers=headers)
    data = r.json()
    checksum = Checksum.generate_md5(r.content)
    return {"data": data, "checksum": checksum}
