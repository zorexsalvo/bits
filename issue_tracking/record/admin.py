from django.contrib import admin
from .models import User, Issue, Ticket, Company, Tracker



admin.site.register(Company)
admin.site.register(Issue)
admin.site.register(Ticket)
admin.site.register(User)
admin.site.register(Tracker)
admin.site.site_header = 'Issue Tracking System'
