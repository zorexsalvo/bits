from django.contrib import admin
from django.contrib.auth.models import Group
from maintenance.models import Issue, Representative, Ticket, Repository


class TicketInline(admin.StackedInline):
    extra = 0
    model = Ticket
    fields = ('issue', 'remark', 'note')
    readonly_fields = ('issue', 'remark', 'note')


class IssueAdmin(admin.ModelAdmin):
    inlines = [TicketInline,]
    search_fields = ('reference_number', 'title', 'created_by')
    list_display = ('reference_number', 'title', 'created_by', 'date_created')
    readonly_fields = ('date_created',)


class RepresentativeAdmin(admin.ModelAdmin):
    inlines = [TicketInline,]
    search_fields = ('reference_number', 'first_name', 'middle_name', 'last_name')
    list_display = ('first_name', 'middle_name', 'last_name')


class TicketAdmin(admin.ModelAdmin):
    search_fields = ('representative', 'issue', 'reference_number', 'remark')
    list_display = ('issue', 'representative', 'reference_number', 'remark', 'created_by', 'date_created')


admin.site.unregister(Group)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Representative, RepresentativeAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Repository)
admin.site.site_header = 'Issue Tracking System'
