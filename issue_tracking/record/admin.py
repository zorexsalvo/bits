from django.contrib import admin
from .models import *

admin.site.register(Company)
admin.site.register(Issue)
admin.site.register(Thread)
admin.site.register(User)
admin.site.register(Tracker)
admin.site.register(Notification)
admin.site.register(SmsNotification)
admin.site.site_header = 'Issue Tracking System'
