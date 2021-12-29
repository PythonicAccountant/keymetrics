import logging
from typing import Optional

import requests
from pyrate_limiter import Duration, Limiter, RequestRate

from config.settings.base import env
from keymetrics.financials.models import Checksum

limiter = Limiter(RequestRate(10, Duration.SECOND))


@limiter.ratelimit("SEC", delay=True)
def get_sec_data(url: str) -> Optional[dict]:
    """
    Get SEC API data and checksum given a URL

    :param url: URL of SEC API
    :return: Dictionary of response data (JSON) and MD5 checksum of the JSON content
    """

    try:
        headers = {"User-Agent": env("SEC_API_USER_AGENT")}
        r = requests.get(url, headers=headers, timeout=3)
        r.raise_for_status()
        data = r.json()
        checksum = Checksum.generate_md5(r.content)
        return {"data": data, "checksum": checksum}
    except requests.exceptions.HTTPError as errh:
        logging.critical(errh, exc_info=True)
    except requests.exceptions.ConnectionError as errc:
        logging.critical(errc, exc_info=True)
    except requests.exceptions.Timeout as errt:
        logging.critical(errt, exc_info=True)
    except requests.exceptions.RequestException as err:
        logging.critical(err, exc_info=True)
    return None
