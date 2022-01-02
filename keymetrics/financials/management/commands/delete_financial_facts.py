from django.core.management.base import BaseCommand

from keymetrics.financials.models import Checksum, Filing


def delete_data():
    Filing.objects.all().delete()
    Checksum.objects.all().delete()


class Command(BaseCommand):
    def handle(self, *args, **options):
        delete_data()
