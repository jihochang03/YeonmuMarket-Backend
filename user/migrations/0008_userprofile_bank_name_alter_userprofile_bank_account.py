# Generated by Django 5.0.6 on 2024-10-04 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_remove_userprofile_remaining_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='bank_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='bank_account',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
