# Generated by Django 3.2.10 on 2021-12-21 19:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('financials', '0019_auto_20211221_1619'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='ticker',
        ),
        migrations.CreateModel(
            name='Ticker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=20, unique=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickers', to='financials.company')),
            ],
        ),
    ]
