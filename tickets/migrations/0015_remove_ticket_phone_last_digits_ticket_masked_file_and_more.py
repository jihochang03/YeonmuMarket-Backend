# Generated by Django 5.0.6 on 2024-10-19 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0014_ticket_booking_details_ticket_transferee_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='phone_last_digits',
        ),
        migrations.AddField(
            model_name='ticket',
            name='masked_file',
            field=models.FileField(blank=True, null=True, upload_to='tickets/masked/'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='processed_seat_image',
            field=models.FileField(blank=True, null=True, upload_to='tickets/seats/processed/'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='uploaded_file',
            field=models.FileField(blank=True, null=True, upload_to='tickets/'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='uploaded_seat_image',
            field=models.FileField(blank=True, null=True, upload_to='tickets/seats/'),
        ),
    ]