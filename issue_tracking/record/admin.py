from django.contrib import admin
from .models import *

class IssueAdmin(admin.ModelAdmin):
    search_fields = ('reference_id', 'title',)
    list_filter = ('priority', 'decision',)
    list_display = ('reference_id', 'title', 'assigned_to',
                    'priority', 'decision', 'created_by',)


class NotificationAdmin(admin.ModelAdmin):
    search_fields = ('user',)
    list_filter = ('category',)
    list_display = ('user', 'category', 'title',)


class SmsNotificationAdmin(admin.ModelAdmin):
    list_display = ('sms', 'priority',)


class ThreadAdmin(admin.ModelAdmin):
    list_display = ('issue', 'note',)

admin.site.register(Company)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(User)
admin.site.register(Tracker)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(SmsNotification, SmsNotificationAdmin)
admin.site.site_header = 'Issue Tracking System'
