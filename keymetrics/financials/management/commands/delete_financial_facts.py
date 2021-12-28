from django.core.management.base import BaseCommand

from keymetrics.financials.models import Filing


def delete_data():
    Filing.objects.all().delete()


class Command(BaseCommand):
    def handle(self, *args, **options):
        delete_data()
