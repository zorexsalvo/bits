from django.contrib import admin
from django.contrib.auth.models import Group
from maintenance.models import User, Issue, Ticket


class TicketInline(admin.StackedInline):
    extra = 0
    model = Ticket
    fields = ('assigned_to', 'issue', 'remark', 'note', 'date_created', 'created_by')
    readonly_fields = ('date_created', 'created_by')

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'author', None) is None:
            obj.created_by = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(TicketInline, self).get_queryset(request)
        qs = qs.order_by('id')
        return qs


class IssueAdmin(admin.ModelAdmin):
    inlines = [TicketInline,]
    search_fields = ('title', 'created_by', 'reference_id')
    list_display = ('reference_id', 'title', 'created_by', 'date_created')
    fields = ('title', 'created_by', 'date_created')
    readonly_fields = ('date_created', 'created_by')

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'author', None) is None:
            obj.created_by = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(IssueAdmin, self).get_queryset(request)
        qs = qs.order_by('id')
        return qs


class UserAdmin(admin.ModelAdmin):
    inlines = [TicketInline,]
    search_fields = ('first_name', 'middle_name', 'last_name')
    list_display = ('first_name', 'middle_name', 'last_name', 'sex', 'date_of_birth')
    readonly_fields = ('date_created', 'created_by')

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'author', None) is None:
            obj.created_by = request.user
        obj.save()


class TicketAdmin(admin.ModelAdmin):
    search_fields = ('assigned_to', 'issue', 'reference_id', 'remark')
    list_display = ('reference_id', 'issue', 'assigned_to', 'remark', 'created_by', 'date_created')
    fields = ('issue', 'assigned_to', 'remark', 'note', 'created_by', 'date_created')
    readonly_fields = ('date_created', 'created_by')
    list_filter = ('remark',)

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'author', None) is None:
            obj.created_by = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(TicketAdmin, self).get_queryset(request)
        qs = qs.order_by('id')
        return qs


admin.site.unregister(Group)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(User, UserAdmin)
admin.site.site_header = 'Issue Tracking System'
