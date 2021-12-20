# Generated by Django 3.2.10 on 2021-12-17 00:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('ticker', models.CharField(max_length=25)),
                ('CIK', models.CharField(max_length=25)),
            ],
            options={
                'verbose_name_plural': 'companies',
            },
        ),
        migrations.CreateModel(
            name='Filing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('10Q', '10-Q'), ('10K', '10-K')], max_length=5)),
                ('date_filed', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='FinancialConcept',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Financial Concept Name')),
                ('unit', models.CharField(max_length=50)),
                ('type', models.CharField(choices=[('ao', 'As of'), ('pe', 'Period ended')], max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='FinancialFact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='TimeDimension',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField()),
                ('months', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name='timedimension',
            constraint=models.UniqueConstraint(fields=('start_date', 'end_date', 'months'), name='unique_time_dimension'),
        ),
        migrations.AddField(
            model_name='financialfact',
            name='concept',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_facts', to='financials.financialconcept'),
        ),
        migrations.AddField(
            model_name='financialfact',
            name='filing',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_facts', to='financials.filing'),
        ),
        migrations.AddField(
            model_name='financialfact',
            name='period',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_facts', to='financials.timedimension'),
        ),
        migrations.AddField(
            model_name='filing',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filings', to='financials.company'),
        ),
    ]
