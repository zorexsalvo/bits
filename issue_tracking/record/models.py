from __future__ import unicode_literals
from django.contrib.auth.models import User as AuthUser
from django.core.validators import RegexValidator
from django.db import models

from django.db.models.signals import post_save
from django.dispatch import receiver

from issue_tracker.roles import Administrator, Employee
from issue_tracker.config import sys_config

from colorfield.fields import ColorField

PHONE_REGEX = RegexValidator(regex=r'^\b(09)\d{9}?\b$', message='Phone number must be entered in the format: 09XXXXXXXXXX.')
NAME_REGEX = RegexValidator(regex=r'^[a-zA-Z\xd1\xf1\s.-]*$', message='Invalid input.')
GLOBE_LABS_CONFIG_SECTION = 'GlobeLabs'


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
    color = models.CharField(max_length=200, null=True)
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
        if not self.reference_id:
            Issue.objects.filter(id=self.id).update(reference_id='#{0:04d}'.format(count))

        url = '/trackers/{}/issues/'.format(self.tracker.id)

        if self.assigned_to:
            if self.assigned_to.type == 'EMPLOYEE':
                url += 'employee/'

            if self.assigned_to:
                title = '{} assigned you in an issue.'.format(self.created_by)

                Notification.objects.create(user=self.assigned_to,
                                            category='ISSUE',
                                            title=title,
                                            url=url,
                                            read=False)


class Thread(models.Model):
    CALLOUTS = (('FYI', 'For Your Information'),
                ('FC', 'For Compliance'),
                ('FV', 'For Verication'),
                ('ASAP', 'For Immediate Action'),
                ('F/UP', 'Follow-Up'),
                ('NA', 'Not Applicable'),
                ('OK', 'Noted'),
                ('FD', 'For Decision'))

    issue = models.ForeignKey(Issue, related_name='threads')
    assigned_to = models.ForeignKey(User, related_name='threads', null=True)
    note = models.TextField()
    callout = models.CharField(max_length=200, choices=CALLOUTS, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='threads_created')

    def __unicode__(self):
        return str(self.issue)

    def send_sms_notification(self, thread):
        sender_address = sys_config.get(GLOBE_LABS_CONFIG_SECTION, 'short_code')
        sms_uri = sys_config.get(GLOBE_LABS_CONFIG_SECTION, 'sms_uri').format(senderAddress=sender_address, access_token=issue.assigned_to.access_token)

        sms_notification = '{created_by} assigned you in an issue. {reference_id} - {title}'

        if sms_notification is not None:
            sms_payload = {
                'address': thread.issue.assigned_to.mobile_number,
                'message': sms_notification.format(reference_id=thread.issue.reference_id, title=thread.issue.title, created_by=thread.created_by)
            }

            try:
                response = requests.post(sms_uri, data=sms_payload)
                logging.info(response.text)
            except requests.exceptions.ProxyError as e:
                logging.error(e)
            except requests.exceptions.ConnectionError as f:
                logging.error(f)

    def save(self, *args, **kwargs):
        thread = super(Thread, self).save(*args, **kwargs)

        tags = []

        url = '/trackers/{}/issues/'.format(self.issue.tracker.id)
        if self.assigned_to.type == 'EMPLOYEE':
            url += 'employee/'

        if not self.issue.created_by == self.created_by:
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

                        title = '{} tagged you in an issue.'.format(self.created_by)
                        user = User.objects.filter(username__username__icontains=tag[1:]).first()

                        Notification.objects.create(user=user,
                                                    category='THREAD',
                                                    title=title,
                                                    url=url,
                                                    read=False)

        if not self.created_by == self.issue.assigned_to:
            self.send_sms_notification(thread)


class SmsNotification(models.Model):
    PRIORITY = (('LOW', 'Low'),
                ('NORMAL', 'Normal'),
                ('HIGH', 'High'),
                ('EMERGENCY', 'Emergency'))

    sms = models.TextField()
    priority = models.CharField(max_length=200, choices=PRIORITY)
    active = models.BooleanField()
