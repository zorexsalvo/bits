from django.contrib import admin
from django.contrib.auth.models import Group
from maintenance.models import Issue, Representative, Ticket

# Register your models here.
admin.site.unregister(Group)
admin.site.register(Issue)
admin.site.register(Representative)
admin.site.register(Ticket)
admin.site.site_header = 'Issue Tracking System'
