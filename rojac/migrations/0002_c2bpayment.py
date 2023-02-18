# Generated by Django 4.1.1 on 2022-09-21 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rojac", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="C2BPayment",
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
                    "TransactionType",
                    models.CharField(blank=True, max_length=12, null=True),
                ),
                ("TransID", models.CharField(blank=True, max_length=12, null=True)),
                ("TransTime", models.CharField(blank=True, max_length=14, null=True)),
                ("TransAmount", models.CharField(blank=True, max_length=12, null=True)),
                (
                    "BusinessShortCode",
                    models.CharField(blank=True, max_length=6, null=True),
                ),
                (
                    "BillRefNumber",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "InvoiceNumber",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "OrgAccountBalance",
                    models.CharField(blank=True, max_length=12, null=True),
                ),
                (
                    "ThirdPartyTransID",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("MSISDN", models.CharField(blank=True, max_length=12, null=True)),
                ("FirstName", models.CharField(blank=True, max_length=20, null=True)),
                ("MiddleName", models.CharField(blank=True, max_length=20, null=True)),
                ("LastName", models.CharField(blank=True, max_length=20, null=True)),
            ],
        ),
    ]
