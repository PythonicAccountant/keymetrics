from django.core.management.base import BaseCommand

from keymetrics.financials.models import Company


def reset_tracked_companies():
    obs = Company.objects.all()
    for company in obs:
        company.istracked = False
    Company.objects.bulk_update(obs, ["istracked"])


def update_tracked_companies(tracked_companies_list):
    obs = [Company.objects.get(ticker=t) for t in tracked_companies_list]
    for company in obs:
        if company.ticker in tracked_companies_list:
            company.istracked = True
    Company.objects.bulk_update(obs, ["istracked"])


class Command(BaseCommand):
    def handle(self, *args, **options):
        reset_tracked_companies()
        tracked_companies_list = [
            "ADBE",
            "AI",
            "AKAM",
            "APPF",
            "APPN",
            "ASAN",
            "ASUR",
            "AVLR",
            "AYX",
            "BIGC",
            "BILL",
            "BL",
            "BLIN",
            "BNFT",
            "BOX",
            "BSY",
            "CCSI",
            "CDAY",
            "CHNG",
            "COUP",
            "CRM",
            "CRWD",
            "CTXS",
            "CXM",
            "DBX",
            "DCT",
            "DDOG",
            "DOCN",
            "DOCU",
            "DOMO",
            "DSGX",
            "DT",
            "ECOM",
            "ESTC",
            "EVBG",
            "FFIV",
            "FIVN",
            "FROG",
            "FSLY",
            "FSSN",
            "GWRE",
            "HUBS",
            "INTU",
            "JAMF",
            "MCHX",
            "MDB",
            "MIME",
            "MIXT",
            "MNDY",
            "MNTV",
            "NCNO",
            "NET",
            "NEWR",
            "NOW",
            "OKTA",
            "OLO",
            "PAYC",
            "PCOR",
            "PCTY",
            "PD",
            "PING",
            "PLAN",
            "QLYS",
            "QTWO",
            "RAMP",
            "RNG",
            "SHOP",
            "SMAR",
            "SNOW",
            "SPLK",
            "SPSC",
            "SPT",
            "SQ",
            "SUMO",
            "TEAM",
            "TEUM",
            "TWLO",
            "TWOU",
            "U",
            "VEEV",
            "VERB",
            "WDAY",
            "WIX",
            "WK",
            "XM",
            "YEXT",
            "ZEN",
            "ZI",
            "ZIP",
            "ZM",
            "ZS",
            "ZUO",
        ]
        update_tracked_companies(tracked_companies_list)
