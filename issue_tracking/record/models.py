from __future__ import unicode_literals
from django.contrib.auth.models import User as AuthUser
from django.core.validators import RegexValidator
from django.db import models

PHONE_REGEX = RegexValidator(regex=r'^\b(09)\d{9}?\b$', message='Phone number must be entered in the format: 09XXXXXXXXXX.')
NAME_REGEX = RegexValidator(regex=r'^[a-zA-Z\xd1\xf1\s.-]*$', message='Invalid input.')


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Companies'


class User(models.Model):
    SEX = (('MALE', 'Male'),
           ('FEMALE', 'Female'))
    TYPE = (('ADMIN', 'Administrator'),
            ('EMPLOYEE', 'Employee'))

    username = models.OneToOneField(AuthUser, related_name='auth_user')
    first_name = models.CharField(max_length=200, validators=[NAME_REGEX])
    middle_name = models.CharField(max_length=200, blank=True, validators=[NAME_REGEX])
    last_name = models.CharField(max_length=200, validators=[NAME_REGEX])
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=200, choices=SEX, default='MALE')
    mobile_number = models.CharField(max_length=13, validators=[PHONE_REGEX])
    company = models.ForeignKey('Company', related_name='users')
    position = models.CharField(max_length=200)
    type = models.CharField(max_length=200, choices=TYPE)
    date_created = models.DateTimeField(auto_now_add=True)
    picture = models.ImageField(upload_to='images')
    created_by = models.CharField(max_length=200)

    def __unicode__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Issue(models.Model):
    PRIORITY = (('LOW', 'Low'),
                ('NORMAL', 'Normal'),
                ('HIGH', 'High'),
                ('EMERGENCY', 'Emergency'))
    REMARKS = (('OPEN', 'Open'),
               ('RESOLVED', 'Resolved'),
               ('CLOSED', 'Closed'))

    reference_id = models.CharField(max_length=200, unique=True, blank=True)
    title = models.CharField(max_length=200)
    assigned_to = models.ForeignKey(User, related_name='issues')
    priority = models.CharField(max_length=200, choices=PRIORITY, default='NORMAL')
    remark = models.CharField(max_length=200, choices=REMARKS, default='OPEN')
    description = models.TextField()

    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='issues_created')

    def __unicode__(self):
        return '{0} - {1}'.format(self.reference_id, self.title)

    def save(self, *args, **kwargs):
        super(Issue, self).save(*args, **kwargs)
        Issue.objects.filter(id=self.id).update(reference_id='#{0:04d}'.format(self.id))


class Thread(models.Model):
    issue = models.ForeignKey(Issue, related_name='threads')
    note = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='threads_created')

    def __unicode__(self):
        return str(self.issue)


class Tracker(models.Model):
    name = models.CharField(max_length=200)
    company = models.ForeignKey(Company, related_name='trackers')

    def __unicode__(self):
        return self.name
