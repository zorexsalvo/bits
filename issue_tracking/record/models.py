from __future__ import unicode_literals
from django.contrib.auth.models import User as AuthUser
from django.core.validators import RegexValidator
from django.db import models

from django.db.models.signals import post_save
from django.dispatch import receiver

from issue_tracker.roles import Administrator, Employee

PHONE_REGEX = RegexValidator(regex=r'^\b(09)\d{9}?\b$', message='Phone number must be entered in the format: 09XXXXXXXXXX.')
NAME_REGEX = RegexValidator(regex=r'^[a-zA-Z\xd1\xf1\s.-]*$', message='Invalid input.')


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Companies'

class Tracker(models.Model):
    name = models.CharField(max_length=200)
    company = models.ForeignKey(Company, related_name='trackers')

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'company')

class User(models.Model):
    SEX = (('MALE', 'Male'),
           ('FEMALE', 'Female'))
    TYPE = (('ADMINISTRATOR', 'Administrator'),
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
    access_token = models.CharField(max_length=200, blank=True, null=True)
    created_by = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        role_map = {
            'ADMINISTRATOR': Administrator,
            'EMPLOYEE': Employee
        }
        target_role = role_map[self.type]
        target_role.assign_role_to_user(self.username)
        super(User, self).save(*args, **kwargs)

    def __unicode__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Notification(models.Model):
    CATEGORY = (('ISSUE', 'Issue'),
                ('THREAD', 'Thread'))

    user = models.ForeignKey(User, related_name='notifications')
    category = models.CharField(max_length=200, choices=CATEGORY, default='ISSUE')
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=200)
    read = models.BooleanField()


class Issue(models.Model):
    PRIORITY = ((None, ''),
                ('LOW', 'Low'),
                ('NORMAL', 'Normal'),
                ('HIGH', 'High'))
    REMARKS = (('OPEN', 'Open'),
               ('CLOSED', 'Closed'),
               ('SLEEP', 'Sleep'),
               ('DEAD', 'Dead'))

    tracker = models.ForeignKey(Tracker)
    reference_id = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200)
    assigned_to = models.ForeignKey(User, related_name='issues', null=True)
    priority = models.CharField(max_length=200, choices=PRIORITY, default=None, null=True)
    decision = models.CharField(max_length=200, choices=REMARKS, default='OPEN')
    description = models.TextField(null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='issues_created')

    def __unicode__(self):
        return '{0} - {1}'.format(self.reference_id, self.title)

    def save(self, *args, **kwargs):
        super(Issue, self).save(*args, **kwargs)
        count = Issue.objects.filter(tracker__id=self.tracker.id).count()
        Issue.objects.filter(id=self.id).update(reference_id='#{0:04d}'.format(count))

        if self.assigned_to:
            url = '/issue/{}/thread/'.format(self.id)
            title = '{} assigned you in an issue.'.format(self.created_by)

            Notification.objects.create(user=self.assigned_to,
                                        category='ISSUE',
                                        title=title,
                                        url=url,
                                        read=False)


class Thread(models.Model):
    issue = models.ForeignKey(Issue, related_name='threads')
    note = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='threads_created')

    def __unicode__(self):
        return str(self.issue)

    def save(self, *args, **kwargs):
        super(Thread, self).save(*args, **kwargs)

        tags = []

        if not self.issue.created_by == self.created_by:
            url = '/issue/{}/thread/'.format(self.issue.id)
            title = '{} replied to your issue.'.format(self.created_by)

            Notification.objects.create(user=self.issue.created_by,
                                        category='THREAD',
                                        title=title,
                                        url=url,
                                        read=False)

            for tag in self.note.split():
                if '@' in tag:
                    print(tag)
                    if User.objects.filter(username__username__icontains=tag[1:]).exists():
                        print('alrigh')

                        title = '{} tagged you in an issue.'.format(self.created_by)
                        user = User.objects.filter(username__username__icontains=tag[1:]).first()

                        Notification.objects.create(user=user,
                                                    category='THREAD',
                                                    title=title,
                                                    url=url,
                                                    read=False)


class SmsNotification(models.Model):
    PRIORITY = (('LOW', 'Low'),
                ('NORMAL', 'Normal'),
                ('HIGH', 'High'),
                ('EMERGENCY', 'Emergency'))

    sms = models.TextField()
    priority = models.CharField(max_length=200, choices=PRIORITY)
    active = models.BooleanField()
