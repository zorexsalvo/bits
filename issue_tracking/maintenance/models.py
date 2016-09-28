from __future__ import unicode_literals
from django.core.validators import RegexValidator
from django.db import models


PHONE_REGEX = RegexValidator(
    regex=r'^+\b(639)\d{9}?\b$',
    message='Phone number must be entered in the format: 639XXXXXXXXXX.')


class Issue(models.Model):
    reference_number = models.CharField(max_length=200, unique=True)
    title = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=200)

    def __str__(self):
        return self.reference_number


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

