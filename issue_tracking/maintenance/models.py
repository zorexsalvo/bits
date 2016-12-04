from __future__ import unicode_literals
from django.contrib.auth.models import User as AuthUser
from django.core.validators import RegexValidator
from django.db import models


PHONE_REGEX = RegexValidator(
    regex=r'^\b(09)\d{9}?\b$',
    message='Phone number must be entered in the format: 09XXXXXXXXXX.')
NAME_REGEX = RegexValidator(
    regex=r'^[a-zA-Z\xd1\xf1\s.-]*$',
message='Invalid input.')


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Companies'


class Issue(models.Model):
    reference_id = models.CharField(max_length=200, unique=True, blank=True)
    title = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=200)

    def __unicode__(self):
        return '{0} - {1}'.format(self.reference_id, self.title)

    def save(self, *args, **kwargs):
        super(Issue, self).save(*args, **kwargs)
        Issue.objects.filter(id=self.id).update(reference_id='#{0:04d}'.format(self.id))


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
        return '{}, {} {}'.format(self.last_name, self.first_name, self.middle_name)


class Ticket(models.Model):
    PRIORITY = (('LOW', 'Low'),
                ('NORMAL', 'Normal'),
                ('HIGH', 'High'),
                ('EMERGENCY', 'Emergency'))
    REMARKS = (('OPEN', 'Open'),
               ('RESOLVED', 'Resolved'),
               ('CLOSED', 'Closed'))

    assigned_to = models.ForeignKey(User, related_name='ticket_repr')
    issue = models.ForeignKey(Issue, related_name='ticket_issue')
    reference_id = models.CharField(max_length=200, unique=True)
    priority = models.CharField(max_length=200, choices=PRIORITY, default='NORMAL')
    remark = models.CharField(max_length=200, choices=REMARKS, default='OPEN')
    note = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=200)

    def __unicode__(self):
        return '{} - {}'.format(self.reference_id, self.assigned_to)

    def save(self, *args, **kwargs):
        super(Ticket, self).save(*args, **kwargs)
        Ticket.objects.filter(id=self.id).update(reference_id='#{0:04d}'.format(self.id))


class Repository(models.Model):
    issue = models.ForeignKey(Issue, related_name='issue_repository')
    ticket = models.ForeignKey(Ticket, related_name='ticket_repository')

    class Meta:
        verbose_name_plural = 'Repositories'

    def __unicode__(self):
        return self.issue


class Tracker(models.Model):
    name = models.CharField(max_length=200)
    company = models.ForeignKey(Company, related_name='trackers')

    def __unicode__(self):
        return self.name
