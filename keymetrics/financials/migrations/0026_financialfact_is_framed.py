# Generated by Django 3.2.10 on 2022-01-03 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("financials", "0025_financialfact_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="financialfact",
            name="is_framed",
            field=models.BooleanField(default=False),
        ),
    ]
