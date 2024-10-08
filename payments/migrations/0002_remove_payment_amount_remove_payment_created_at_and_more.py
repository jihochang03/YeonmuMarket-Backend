# Generated by Django 5.0.6 on 2024-09-13 07:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        ('tickets', '0003_transferhistory_conversation'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='amount',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='payer',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='status',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='transaction_id',
        ),
        migrations.AddField(
            model_name='payment',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payment',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='transfer_request',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='tickets.transferrequest'),
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_number', models.CharField(max_length=100)),
                ('bank_name', models.CharField(max_length=100)),
                ('is_verified', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
