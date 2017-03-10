# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-03-10 11:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0019_auto_20170310_1737'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='callout',
            field=models.CharField(choices=[('FYI', 'For Your Information'), ('FC', 'For Compliance'), ('FV', 'For Verication'), ('ASAP', 'For Immediate Action'), ('F/UP', 'Follow-Up'), ('NA', 'Not Applicable'), ('OK', 'Noted'), ('FD', 'For Decision')], max_length=200, null=True),
        ),
    ]
