# Generated by Django 5.0.6 on 2024-09-13 07:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_remove_payment_amount_remove_payment_created_at_and_more'),
        ('user', '0002_remove_userprofile_kakao_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='bank_account',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='payments.bankaccount'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_payment_verified',
            field=models.BooleanField(default=False),
        ),
    ]