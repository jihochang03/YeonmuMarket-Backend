# Generated by Django 5.0.6 on 2024-09-23 12:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_remove_bankaccount_user_and_more'),
        ('user', '0006_alter_userprofile_bank_account'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BankAccount',
        ),
        migrations.DeleteModel(
            name='Payment',
        ),
    ]
