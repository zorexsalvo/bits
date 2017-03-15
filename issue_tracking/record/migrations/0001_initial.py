# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-01-14 13:48
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Companies',
            },
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_id', models.CharField(blank=True, max_length=200, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issue_repository', to='record.Issue')),
            ],
            options={
                'verbose_name_plural': 'Repositories',
            },
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_id', models.CharField(max_length=200, unique=True)),
                ('priority', models.CharField(choices=[('LOW', 'Low'), ('NORMAL', 'Normal'), ('HIGH', 'High'), ('EMERGENCY', 'Emergency')], default='NORMAL', max_length=200)),
                ('remark', models.CharField(choices=[('OPEN', 'Open'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')], default='OPEN', max_length=200)),
                ('note', models.TextField()),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Tracker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trackers', to='record.Company')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(message='Invalid input.', regex='^[a-zA-Z\\xd1\\xf1\\s.-]*$')])),
                ('middle_name', models.CharField(blank=True, max_length=200, validators=[django.core.validators.RegexValidator(message='Invalid input.', regex='^[a-zA-Z\\xd1\\xf1\\s.-]*$')])),
                ('last_name', models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(message='Invalid input.', regex='^[a-zA-Z\\xd1\\xf1\\s.-]*$')])),
                ('date_of_birth', models.DateField()),
                ('sex', models.CharField(choices=[('MALE', 'Male'), ('FEMALE', 'Female')], default='MALE', max_length=200)),
                ('mobile_number', models.CharField(max_length=13, validators=[django.core.validators.RegexValidator(message='Phone number must be entered in the format: 09XXXXXXXXXX.', regex='^\\b(09)\\d{9}?\\b$')])),
                ('position', models.CharField(max_length=200)),
                ('type', models.CharField(choices=[('ADMIN', 'Administrator'), ('EMPLOYEE', 'Employee')], max_length=200)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('picture', models.ImageField(upload_to='images')),
                ('created_by', models.CharField(max_length=200)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='users', to='record.Company')),
                ('username', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='auth_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='ticket',
            name='assigned_to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_repr', to='record.User'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='issue',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_issue', to='record.Issue'),
        ),
        migrations.AddField(
            model_name='repository',
            name='ticket',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_repository', to='record.Ticket'),
        ),
    ]