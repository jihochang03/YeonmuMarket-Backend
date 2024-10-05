# Generated by Django 5.0.6 on 2024-09-23 12:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conversations', '0005_conversation_acceptance_intent_and_more'),
        ('tickets', '0005_remove_ticket_file_upload_ticket_description_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='conversation',
            old_name='acceptance_intent',
            new_name='is_acceptance_intent',
        ),
        migrations.RenameField(
            model_name='conversation',
            old_name='is_completed',
            new_name='is_transfer_intent',
        ),
        migrations.RemoveField(
            model_name='conversation',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='conversation',
            name='transfer_intent',
        ),
        migrations.RemoveField(
            model_name='conversation',
            name='transferor',
        ),
        migrations.AddField(
            model_name='conversation',
            name='owner',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='conversation_owner', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='conversation',
            name='ticket',
            field=models.OneToOneField(default='', on_delete=django.db.models.deletion.CASCADE, to='tickets.ticket'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='conversation',
            name='transferee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conversation_transferee', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='Message',
        ),
    ]