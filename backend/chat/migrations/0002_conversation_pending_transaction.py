# Generated by Django 5.0.7 on 2025-02-20 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='pending_transaction',
            field=models.JSONField(null=True),
        ),
    ]
