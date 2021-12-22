from django.core.management.base import BaseCommand

from keymetrics.financials.models import Company, TimeDimension


def delete_data():
    TimeDimension.objects.all().delete()


class Command(BaseCommand):
    def handle(self, *args, **options):
        delete_data()
