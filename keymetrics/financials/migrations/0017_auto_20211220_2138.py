# Generated by Django 3.2.10 on 2021-12-20 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financials', '0016_auto_20211220_2101'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='ticker',
            field=models.CharField(default=1, max_length=20),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Ticker',
        ),
    ]
