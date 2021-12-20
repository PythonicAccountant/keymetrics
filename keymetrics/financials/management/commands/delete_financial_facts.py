from django.core.management.base import BaseCommand

from keymetrics.financials.models import FinancialFact


def delete_data():
    FinancialFact.objects.all().delete()


class Command(BaseCommand):
    def handle(self, *args, **options):
        delete_data()
