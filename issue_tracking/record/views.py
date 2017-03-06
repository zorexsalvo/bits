import time
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib import messages

from .forms import *
from .models import Company, User, Tracker, SmsNotification
from issue_tracker.config import sys_config

from issue_tracker.roles import Administrator, Employee
from rolepermissions.mixins import HasRoleMixin

from collections import OrderedDict

import json
import requests
import logging

GLOBE_LABS_CONFIG_SECTION = 'GlobeLabs'

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/user/')


def notification_view(request, notification_id):

    notification = Notification.objects.filter(id=notification_id)
    notification.update(read=True)

    url = notification.first().url

    if request.GET.get('q'):
        url = url + request.GET.get('q')

    return HttpResponseRedirect(url)


def http_403_permission_denied(request):
    return render(request, 'error/403.html')


def http_404_not_found(request):
    return render(request, 'error/404.html')


def http_500_server_error(request):
    return render(request, 'error/500.html')


class UsernameLoginView(TemplateView):
    form_class = UsernameForm
    template_name = 'security/user_login.html'

    def build_url(self, *args, **kwargs):
        url = reverse('login')
        query_params = kwargs.pop('q', None)

        if query_params:
            url += '?username={}'.format(query_params.get('username'))

        return url

    def get(self, request, *args, **kwargs):
        redirect_map = {
            'EMPLOYEE': 'dashboard',
            'ADMINISTRATOR': 'create_company'
        }

        form = self.form_class()
        if request.user.is_authenticated():
            user = User.objects.get(username=request.user)
            url = reverse(redirect_map[user.type])
            return HttpResponseRedirect(url)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            url = self.build_url(reverse('login'), q={'username': form.cleaned_data['username']})
            return HttpResponseRedirect(url)
        return render(request, self.template_name, {'form': form})


class LoginView(TemplateView):
    form_class = LoginForm
    template_name = 'security/login.html'

    def get(self, request, *args, **kwargs):
        user = User.objects.filter(username__username=request.GET.get('username')).first()
        img_url = None

        form = self.form_class({'username': request.GET.get('username')})

        redirect_map = {
            'EMPLOYEE': 'dashboard',
            'ADMINISTRATOR': 'create_company'
        }

        if user is None:
            url = reverse('username_login')
            return HttpResponseRedirect(url)

        if request.user.is_authenticated():
            user = User.objects.get(username=request.user)
            url = reverse(redirect_map[user.type])
            return HttpResponseRedirect(url)
        return render(request, self.template_name, {'form': form, 'user': user})

    def post(self, request, *args, **kwargs):
        redirect_map = {
            'EMPLOYEE': 'dashboard',
            'ADMINISTRATOR': 'create_company'
        }

        username = request.GET.get('username')
        user = User.objects.filter(username__username=username).first()

        if user is None:
            url = reverse('username_login')
            return HttpResponseRedirect(url)

        form = self.form_class(request.POST)
        url = reverse(redirect_map[user.type])
        if form.is_valid():
            user = form.login(request)
            _login = login(request, user)
            return HttpResponseRedirect(url)
        return render(request, self.template_name, {'form': form, 'user':user})


class AdministratorView(HasRoleMixin, TemplateView):
    allowed_roles = [Administrator,]
    def get_companies(self):
        return Company.objects.all()

    def get_user(self, request):
        return  User.objects.filter(username=request.user).first()

    def get_notification(self, request):
        return Notification.objects.filter(user__username=request.user).order_by('-id')

    def get_context(self, request):
        context = {}
        context['companies'] = self.get_companies()
        context['user'] = self.get_user(request)
        context['notifications'] = self.get_notification(request)
        context['unread'] = context['notifications'].filter(read=False)
        return context


class CreateCompany(AdministratorView):
    form_class = CompanyForm
    template_name = 'administrator/create_company.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        form = self.form_class()
        context['form'] = form

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        url = reverse('create_company')
        context = self.get_context(request)
        form = self.form_class(request.POST or None)

        if form.is_valid():
            name = form.cleaned_data.get('name')
            company = Company(name=name)
            company.save()
            messages.success(request, 'Company has created successfully!')
            return HttpResponseRedirect(url)
        else:
            messages.warning(request, 'Company already exists.')
            return HttpResponseRedirect(url)

        context['form'] = self.form_class()
        return render(request, self.template_name, context)


class ViewEmployee(AdministratorView):
    template_name = 'administrator/view_employee.html'

    def get_employees(self):
        return User.objects.all()

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        context['employees'] = self.get_employees()
        return render(request, self.template_name, context)


class CreateEmployee(AdministratorView):
    template_name = 'administrator/create_employee.html'
    form_class = UserForm

    def _save_user(self, username, password):
        user = AuthUser.objects.create_user(username=username, password=password)
        return user

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        context['form'] = self.form_class()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        short_code = sys_config.get(GLOBE_LABS_CONFIG_SECTION, 'short_code')
        cross_telco = sys_config.get(GLOBE_LABS_CONFIG_SECTION, 'cross_telco')
        url = reverse('create_employee')
        context = self.get_context(request)
        form = self.form_class(request.POST or None, request.FILES or None)
        context['form'] = form

        if form.is_valid():
            auth_user = self._save_user(form.cleaned_data.get('username'), form.cleaned_data.get('password'))
            user = User()
            user.username = auth_user
            user.type = form.cleaned_data.get('type')
            user.first_name = form.cleaned_data.get('first_name')
            user.middle_name = form.cleaned_data.get('middle_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.sex = form.cleaned_data.get('sex')
            user.date_of_birth = form.cleaned_data.get('date_of_birth')
            user.mobile_number = form.cleaned_data.get('mobile_number')
            user.company = form.cleaned_data.get('company')
            user.position = form.cleaned_data.get('position')
            user.created_by = request.user
            user.picture = form.cleaned_data.get('picture')
            user.save()
            messages.success(request, 'Text INFO to {} (Cross-telco: {}) to subscribe to SMS Notification.'.format(short_code, cross_telco))
            return HttpResponseRedirect(url)
        else:
            messages.warning(request, 'User already exists.')
            return HttpResponseRedirect(url)
        return render(request, self.template_name, context)


class CreateTracker(AdministratorView):
    template_name = 'administrator/create_tracker.html'
    form_class = TrackerForm

    def get(self, request, company_id, *args, **kwargs):
        context = self.get_context(request)
        context['form'] = self.form_class(initial={'company': company_id})
        context['company'] = Company.objects.get(id=company_id)
        return render(request, self.template_name, context)

    def post(self, request, company_id, *args, **kwargs):
        url = reverse('create_tracker', kwargs={'company_id': company_id})
        context = self.get_context(request)
        company = Company.objects.get(id=company_id)
        form = self.form_class(request.POST or None, initial={'company': company.id})
        context['form'] = form
        context['company'] = company

        if form.is_valid():
            form.save()
            messages.success(request, 'Tracker has been created successfully!')
            return HttpResponseRedirect(url)
        else:
            messages.warning(request, 'Tracker already exists.')
            return HttpResponseRedirect(url)

        return render(request, self.template_name, context)


class AdminIssueView(AdministratorView):
    template_name = 'administrator/issue.html'
    form_class = IssueForm
    respond_form_class = RespondForm

    def build_thread_array(self, count):
        thread = []
        for x in range(count):
            thread.append("")
        return thread

    def get_issue_directory(self, tracker_id):
        issues_directory = {}
        issues = Issue.objects.filter(tracker__id=tracker_id)

        counter = 0
        for issue in issues:
            timestamp = issue.date_created.strftime("%m-%d-%Y %H:%M:%S")
            if timestamp not in issues_directory:
                thread = self.build_thread_array(issues.count())
                thread[counter] = issue.description
                issues_directory[timestamp] = thread
            else:
                issues_directory[timestamp][counter] = issue.description

            for note in issue.threads.all():
                timestamp = note.date_created.strftime("%m-%d-%Y %H:%M:%S")
                if timestamp not in issues_directory:
                    thread = self.build_thread_array(issues.count())
                    thread[counter] = note.note
                    issues_directory[timestamp] = thread
                else:
                    issues_directory[timestamp][counter] = note.note
            counter += 1

        return OrderedDict(sorted(issues_directory.items()))

    def get_issue(self, tracker_id):
        return Issue.objects.filter(tracker__id=tracker_id)

    def send_sms_notification(self, issue):
        issue = Issue.objects.filter(id=issue.id).first()
        sender_address = sys_config.get(GLOBE_LABS_CONFIG_SECTION, 'short_code')
        sms_uri = sys_config.get(GLOBE_LABS_CONFIG_SECTION, 'sms_uri').format(senderAddress=sender_address, access_token=issue.assigned_to.access_token)

        sms_notification = SmsNotification.objects.filter(priority=issue.priority, active=True).first()

        if sms_notification is not None:
            sms_payload = {
                'address': issue.assigned_to.mobile_number,
                'message': sms_notification.sms.format(reference_id=issue.reference_id, title=issue.title, created_by=issue.created_by)
            }

            try:
                response = requests.post(sms_uri, data=sms_payload)
                logging.info(response.text)
            except requests.exceptions.ProxyError as e:
                logging.error(e)
            except requests.exceptions.ConnectionError as f:
                logging.error(f)

    def get(self, request, tracker_id, *args, **kwargs):
        form = self.form_class()
        respond_form = self.respond_form_class(tracker_id)
        context = self.get_context(request)
        context['issues'] = self.get_issue(tracker_id)
        context['issue_directory'] = self.get_issue_directory(tracker_id)
        context['tracker'] = Tracker.objects.get(id=tracker_id)
        context['form'] = form
        context['respond_form'] = respond_form
        context['active_tracker'] = tracker_id
        return render(request, self.template_name, context)

    def post(self, request, tracker_id, *args, **kwargs):
        form = self.form_class(request.POST or None)
        respond_form = self.respond_form_class(tracker_id, request.POST or None)
        context = self.get_context(request)
        context['issues'] = self.get_issue(tracker_id)
        context['issue_directory'] = self.get_issue_directory(tracker_id)
        context['respond_form'] = respond_form
        context['active_tracker'] = tracker_id
        context['tracker'] = Tracker.objects.get(id=tracker_id)
        context['form'] = form

        if form.is_valid():
            url = reverse('admin_tracker_issue', kwargs={'tracker_id':tracker_id})
            data = form.cleaned_data
            data['tracker'] = Tracker.objects.get(id=tracker_id)
            data['created_by'] = User.objects.get(username=request.user)
            issue = Issue.objects.create(**data)
            self.send_sms_notification(issue)
            return HttpResponseRedirect(url)

        if respond_form.is_valid():
            url = reverse('admin_tracker_issue', kwargs={'tracker_id':tracker_id})
            data = respond_form.cleaned_data
            issue = Issue.objects.get(id=data.get('issue_id'))
            thread = Thread(issue=issue,
                            note=data.get('message'),
                            created_by=User.objects.get(username=request.user))
            thread.save()
            return HttpResponseRedirect(url)

        return render(request, self.template_name, context)


class UpdateEmployee(AdministratorView):
    template_name = 'administrator/update_employee.html'
    form_class = UpdateUserForm

    def get(self, request, employee_id, *args, **kwargs):
        context = self.get_context(request)
        user = User.objects.get(pk=employee_id)
        form = self.form_class(instance=user)
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request, employee_id, *args, **kwargs):
        url = reverse('update_employee', kwargs={'employee_id': employee_id})
        user = User.objects.get(id=employee_id)
        form = self.form_class(request.POST or None, request.FILES or None, instance=user)
        context = self.get_context(request)
        context['form'] = form

        if form.is_valid():
            user = User.objects.get(id=employee_id)
            user.first_name = form.cleaned_data.get('first_name')
            user.middle_name = form.cleaned_data.get('middle_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.sex = form.cleaned_data.get('sex')
            user.date_of_birth = form.cleaned_data.get('date_of_birth')
            user.mobile_number = form.cleaned_data.get('mobile_number')
            user.company = form.cleaned_data.get('company')
            user.position = form.cleaned_data.get('position')
            user.picture = form.cleaned_data.get('picture')
            user.save()
            messages.success(request, 'Employee has been updated successfully.')
            return HttpResponseRedirect(url)
        else:
            print(form.errors)
            messages.warning(request, 'Update is not successful.')
            return HttpResponseRedirect(url)

        return render(request, self.template_name, context)


class DeleteEmployee(AdministratorView):
    def get(self, request, employee_id, *args, **kwargs):
        url = reverse('view_employee')
        user = User.objects.filter(id=employee_id)
        user.delete()
        return HttpResponseRedirect(url)


class AdminThreadView(AdministratorView):
    template_name = 'administrator/thread.html'
    form_class = ThreadForm

    def get_object(self, issue_id):
        try:
            return Issue.objects.get(id=issue_id)
        except Issue.DoesNotExist:
            None

    def get(self, request, issue_id, *args, **kwargs):
        context = self.get_context(request)
        context['form'] = self.form_class()
        context['issue'] = self.get_object(issue_id)
        context['thread'] = Thread.objects.filter(issue__id=issue_id)

        return render(request, self.template_name, context)

    def post(self, request, issue_id, *args, **kwargs):
        context = self.get_context(request)
        form = self.form_class(request.POST or None)
        context['form'] = form
        context['issue'] = self.get_object(issue_id)
        context['thread'] = Thread.objects.filter(issue__id=issue_id)

        if form.is_valid():
            data = form.cleaned_data
            data['issue'] = Issue.objects.get(id=issue_id)
            data['created_by'] = User.objects.get(username=request.user)
            Thread.objects.create(**data)

        context['form'] = self.form_class()
        return render(request, self.template_name, context)


class EmployeeView(HasRoleMixin, TemplateView):
    allowed_roles = [Employee,]

    def get_user(self, request):
        return  User.objects.filter(username=request.user).first()

    def get_notification(self, request):
        return Notification.objects.filter(user__username=request.user).order_by('-id')

    def get_context(self, request):
        context = {}
        context['user'] = self.get_user(request)
        context['notifications'] = self.get_notification(request)
        context['unread'] = context['notifications'].filter(read=False)
        return context


class DashboardView(EmployeeView):
    template_name = 'user/index.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        return render(request, self.template_name, context)


class IssueView(EmployeeView):
    template_name = 'user/issue.html'
    form_class = IssueForm

    def get_issue(self, user):
        if user:
            return Issue.objects.filter(created_by__company__id=user.company.id).order_by('-id')
        return Issue.objects.all()

    def send_sms_notification(self, issue):
        issue = Issue.objects.filter(id=issue.id).first()
        sender_address = sys_config.get(GLOBE_LABS_CONFIG_SECTION, 'short_code')
        sms_uri = sys_config.get(GLOBE_LABS_CONFIG_SECTION, 'sms_uri').format(senderAddress=sender_address, access_token=issue.assigned_to.access_token)

        sms_notification = SmsNotification.objects.filter(priority=issue.priority, active=True).first()

        if sms_notification is not None:
            sms_payload = {
                'address': issue.assigned_to.mobile_number,
                'message': sms_notification.sms.format(reference_id=issue.reference_id, title=issue.title, created_by=issue.created_by)
            }

            try:
                response = requests.post(sms_uri, data=sms_payload)
                logging.info(response.text)
            except requests.exceptions.ProxyError as e:
                logging.error(e)
            except requests.exceptions.ConnectionError as f:
                logging.error(f)

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = self.get_context(request)
        context['issues'] = self.get_issue(context['user'])
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST or None)
        context = self.get_context(request)
        context['issues'] = self.get_issue(context['user'])
        context['form'] = form

        if form.is_valid():
            url = reverse('issue')
            data = form.cleaned_data
            data['created_by'] = User.objects.get(username=request.user)
            issue = Issue.objects.create(**data)
            self.send_sms_notification(issue)
            return HttpResponseRedirect(url)
        return render(request, self.template_name, context)


class UserDirectoryView(EmployeeView):
    template_name = 'user/user.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        context['users'] = User.objects.all()
        return render(request, self.template_name, context)


class CheckView(EmployeeView):
    template_name = 'user/check.html'
    form_class = CheckForm

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        context['form'] = self.form_class()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context(request)
        form = self.form_class(request.POST or None)

        if form.is_valid():
            context['record'] = Issue.objects.filter(reference_id__icontains=form.cleaned_data.get('keyword')).first()

        context['form'] = self.form_class()
        return render(request, self.template_name, context)


class ThreadView(EmployeeView):
    template_name = 'user/thread.html'
    form_class = ThreadForm

    def get_object(self, issue_id):
        try:
            return Issue.objects.get(id=issue_id)
        except Issue.DoesNotExist:
            None

    def get(self, request, issue_id, *args, **kwargs):
        context = self.get_context(request)
        context['form'] = self.form_class()
        context['issue'] = self.get_object(issue_id)
        context['thread'] = Thread.objects.filter(issue__id=issue_id)
        return render(request, self.template_name, context)

    def post(self, request, issue_id, *args, **kwargs):
        context = self.get_context(request)
        form = self.form_class(request.POST or None)
        context['form'] = form
        context['issue'] = self.get_object(issue_id)
        context['thread'] = Thread.objects.filter(issue__id=issue_id)

        if form.is_valid():
            data = form.cleaned_data
            data['issue'] = Issue.objects.get(id=issue_id)
            data['created_by'] = User.objects.get(username=request.user)
            Thread.objects.create(**data)

        context['form'] = self.form_class()
        return render(request, self.template_name, context)


@method_decorator(csrf_exempt, name='dispatch')
class SMSView(View):
    def get(self, request, *args, **kwargs):
        access_token = self.request.GET.get('access_token')
        subscriber_number = self.request.GET.get('subscriber_number')

        User.objects.filter(mobile_number__endswith=subscriber_number).update(access_token=access_token)
        return HttpResponse()

    def post(self, request, *args, **kwargs):
        unsubscribed = json.loads(self.request.body).get('unsubscribed')

        User.objects.filter(mobile_number__endswith=unsubscribed.get('subscriber_number')).update(access_token=None)
        return HttpResponse()
