# Generated by Django 5.0.6 on 2024-12-31 08:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tickets', '0024_remove_ticket_status_ticket_istransfer_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Exchange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_step', models.IntegerField(default=0)),
                ('is_transfer_intent', models.BooleanField(default=False)),
                ('is_acceptance_intent', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owner_exchange', to=settings.AUTH_USER_MODEL)),
                ('ticket_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exchanges_as_ticket_1', to='tickets.ticket')),
                ('ticket_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exchanges_as_ticket_2', to='tickets.ticket')),
                ('transferee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transferee_exchange', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
