# Generated by Django 5.0.6 on 2024-12-21 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0022_remove_ticket_keyword'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='masked_file',
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='processed_seat_image',
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='uploaded_file',
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='uploaded_seat_image',
        ),
        migrations.AddField(
            model_name='ticket',
            name='masked_file_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='processed_seat_image_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='uploaded_file_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='uploaded_seat_image_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
