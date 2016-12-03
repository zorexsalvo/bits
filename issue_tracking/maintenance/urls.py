from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'login/$', LoginView.as_view(), name='login'),
    url(r'logout/$', logout_view, name='logout'),
    url(r'create_company/$', CreateCompany.as_view(), name='create_company'),
    url(r'view_employee/$', ViewEmployee.as_view(), name='view_employee'),
    url(r'create_employee/$', CreateEmployee.as_view(), name='create_employee')
]
