# Generated by Django 5.0.6 on 2024-09-13 07:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conversations', '0003_remove_conversation_created_at_and_more'),
        ('tickets', '0002_remove_transferhistory_chat_room'),
    ]

    operations = [
        migrations.AddField(
            model_name='transferhistory',
            name='conversation',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='conversations.conversation'),
        ),
    ]
