from django.contrib.auth.decorators import login_required
from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'login/user/$', UsernameLoginView.as_view(), name='username_login'),
    url(r'^$', LoginView.as_view(), name='login'),
    url(r'logout/$', login_required(logout_view), name='logout'),
    url(r'notifications/(?P<notification_id>\d+)/$', notification_view, name='notification'),
    url(r'settings/$', login_required(AdministratorSettings.as_view()), name='settings'),
    url(r'companies/create/$', login_required(CreateCompany.as_view()), name='create_company'),
    url(r'companies/(?P<company_id>\d+)/trackers/create/$', login_required(CreateTracker.as_view()), name='create_tracker'),
    url(r'trackers/(?P<tracker_id>\d+)/issues/$', login_required(AdminIssueView.as_view()), name='admin_tracker_issue'),
    url(r'issues/(?P<issue_id>\d+)/$', login_required(AdminThreadView.as_view()), name='admin_issue_thread'),
    url(r'companies/(?P<company_id>\d+)/employees/$', login_required(ViewEmployee.as_view()), name='view_employee'),
    url(r'employees/create/$', login_required(CreateEmployee.as_view()), name='create_employee'),
    url(r'employees/(?P<employee_id>\d+)/update/$', login_required(UpdateEmployee.as_view()), name='update_employee'),
    url(r'employees/(?P<employee_id>\d+)/delete/$', login_required(DeleteEmployee.as_view()), name='delete_employee'),
    url(r'dashboard/admin/$', login_required(AdminDashboard.as_view()), name='admin_dashboard'),
    url(r'archive/$', login_required(ArchiveView.as_view()), name='archive'),
    url(r'dashboard/$', login_required(DashboardView.as_view()), name='dashboard'),
    url(r'trackers/(?P<tracker_id>\d+)/issues/employee/$', login_required(IssueView.as_view()), name='issue'),
    url(r'archive/employee/$', login_required(EmployeeArchiveView.as_view()), name='archive_employee'),
    url(r'v1/notify_uri', SMSView.as_view(), name='notify_uri'),
]
