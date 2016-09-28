from django.contrib import admin
from django.contrib.auth.models import Group
from maintenance.models import Issue

# Register your models here.
admin.site.unregister(Group)
admin.site.register(Issue)
admin.site.site_header = 'Issue Tracking System'
