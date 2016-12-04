# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-04 15:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0018_tracker'),
    ]

    operations = [
        migrations.AddField(
            model_name='tracker',
            name='company',
            field=models.ForeignKey(default=52, on_delete=django.db.models.deletion.CASCADE, related_name='trackers', to='maintenance.Company'),
            preserve_default=False,
        ),
    ]
