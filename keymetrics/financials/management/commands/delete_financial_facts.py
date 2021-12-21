from django.core.management.base import BaseCommand

from keymetrics.financials.models import Company


def delete_data():
    Company.objects.all().delete()


class Command(BaseCommand):
    def handle(self, *args, **options):
        delete_data()
