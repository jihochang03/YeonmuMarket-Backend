# Generated by Django 5.0.6 on 2024-09-23 02:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_transferhistory_conversation'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='file_upload',
            field=models.FileField(blank=True, null=True, upload_to='ticket_files/'),
        ),
    ]