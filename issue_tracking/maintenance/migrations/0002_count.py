# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-29 13:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Count',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issue', models.IntegerField(default=0)),
                ('representative', models.IntegerField(default=0)),
                ('ticket', models.IntegerField(default=0)),
            ],
        ),
    ]
