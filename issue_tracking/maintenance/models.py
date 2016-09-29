from __future__ import unicode_literals
from django.core.validators import RegexValidator
from django.db import models


PHONE_REGEX = RegexValidator(
    regex=r'^\b(09)\d{9}?\b$',
    message='Phone number must be entered in the format: 09XXXXXXXXXX.')


class Issue(models.Model):
    reference_number = models.CharField(max_length=200, unique=True)
    title = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=200)

    def __str__(self):
        return '{} - {}'.format(self.reference_number, self.title)


class Representative(models.Model):
    SEX = (('MALE', 'Male'),
           ('FEMALE', 'Female'))

    reference_number = models.CharField(max_length=200, unique=True)
    first_name = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=200, choices=SEX, default='Male')
    mobile_number = models.CharField(max_length=13, validators=[PHONE_REGEX])
    email_address = models.EmailField(max_length=200, blank=True, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=200)

    def __str__(self):
        return '{}, {} {}'.format(self.last_name, self.first_name, self.middle_name)


class Ticket(models.Model):
    REMARKS = (('LOW', 'Low'),
               ('NORMAL', 'Normal'),
               ('HIGH', 'High'),
               ('EMERGENCY', 'Emergency'))

    representative = models.ForeignKey(Representative, related_name='ticket_repr')
    issue = models.ForeignKey(Issue, related_name='ticket_issue')
    reference_number = models.CharField(max_length=200, unique=True)
    remark = models.CharField(max_length=200, choices=REMARKS, default='NORMAL')
    note = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=200)

    def __str__(self):
        return '{} - {}'.format(self.reference_number, self.representative)


class Repository(models.Model):
    issue = models.ForeignKey(Issue, related_name='issue_repository')
    ticket = models.ForeignKey(Ticket, related_name='ticket_repository')

    class Meta:
        verbose_name_plural = 'Repositories'

    def __str__(self):
        return self.issue

