# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-03 14:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0016_user_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='type',
            field=models.CharField(choices=[('ADMIN', 'Administrator'), ('EMPLOYEE', 'Employee')], max_length=200),
        ),
    ]
