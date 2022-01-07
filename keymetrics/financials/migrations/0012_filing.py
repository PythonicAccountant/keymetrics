# Generated by Django 3.2.10 on 2021-12-18 07:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("financials", "0011_alter_company_ticker"),
    ]

    operations = [
        migrations.CreateModel(
            name="Filing",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("10-Q", "10-Q"),
                            ("10-K", "10-K"),
                            ("10-Q/A", "10-Q/A"),
                            ("10-K/A", "10-K/A"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "accn_num",
                    models.CharField(
                        max_length=255, unique=True, verbose_name="Accession Number"
                    ),
                ),
                ("date_filed", models.DateField()),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="filings",
                        to="financials.company",
                    ),
                ),
            ],
        ),
    ]
