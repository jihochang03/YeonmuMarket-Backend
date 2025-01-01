# Generated by Django 5.0.6 on 2024-12-31 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0023_remove_ticket_masked_file_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='status',
        ),
        migrations.AddField(
            model_name='ticket',
            name='isTransfer',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='status_exchange',
            field=models.CharField(choices=[('waiting', '교환자 대기'), ('exchange_pending', '교환 중'), ('exchange_completed', '교환 완료')], default='waiting', max_length=20),
        ),
        migrations.AddField(
            model_name='ticket',
            name='status_transfer',
            field=models.CharField(choices=[('waiting', '양수자 대기'), ('transfer_pending', '양도 중'), ('transfer_completed', '양도 완료')], default='waiting', max_length=20),
        ),
    ]