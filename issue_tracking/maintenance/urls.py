from django.contrib.auth.decorators import login_required
from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'login/$', LoginView.as_view(), name='login'),
    url(r'logout/$', login_required(logout_view), name='logout'),
    url(r'create_company/$', login_required(CreateCompany.as_view()), name='create_company'),
    url(r'view_employee/$', login_required(ViewEmployee.as_view()), name='view_employee'),
    url(r'create_employee/$', login_required(CreateEmployee.as_view()), name='create_employee'),
    url(r'create_tracker/(?P<company_id>\d+)/$', login_required(CreateTracker.as_view()), name='create_tracker'),
    url(r'dashboard/$', login_required(DashboardView.as_view()), name='dashboard'),
    url(r'issue/$', login_required(IssueView.as_view()), name='issue'),
    url(r'user/$', login_required(UserDirectoryView.as_view()), name='user_directory'),
    url(r'check/$', login_required(CheckView.as_view()), name='check')
]
