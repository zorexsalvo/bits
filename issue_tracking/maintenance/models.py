from __future__ import unicode_literals

from django.db import models

class Issue(models.Model):
    issue_no = models.CharField(max_length=200, unique=True)
    remarks = models.CharField(max_length=200)
    note = models.TextField()
