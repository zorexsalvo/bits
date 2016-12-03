from django.contrib.auth.decorators import login_required
from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'login/$', LoginView.as_view(), name='login'),
    url(r'logout/$', login_required(logout_view), name='logout'),
    url(r'create_company/$', login_required(CreateCompany.as_view()), name='create_company'),
    url(r'view_employee/$', login_required(ViewEmployee.as_view()), name='view_employee'),
    url(r'create_employee/$', login_required(CreateEmployee.as_view()), name='create_employee')
]
