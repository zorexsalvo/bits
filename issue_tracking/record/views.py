import time
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User as AuthUser
from django.db.models import Q

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
            'ADMINISTRATOR': 'admin_dashboard'
        }

        logo = Utility.objects.first()
        form = self.form_class()
        if request.user.is_authenticated():
            user = User.objects.get(username=request.user)
            url = reverse(redirect_map[user.type])
            return HttpResponseRedirect(url)
        return render(request, self.template_name, {'form': form, 'logo': logo})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        logo = Utility.objects.first()

        if form.is_valid():
            url = self.build_url(reverse('login'), q={'username': form.cleaned_data['username']})
            return HttpResponseRedirect(url)
        return render(request, self.template_name, {'form': form, 'logo': logo})


class LoginView(TemplateView):
    form_class = LoginForm
    template_name = 'security/login.html'

    def get(self, request, *args, **kwargs):
        user = User.objects.filter(username__username=request.GET.get('username')).first()
        img_url = None
        logo = Utility.objects.first()

        form = self.form_class({'username': request.GET.get('username')})

        redirect_map = {
            'EMPLOYEE': 'dashboard',
            'ADMINISTRATOR': 'admin_dashboard'
        }

        if user is None:
            url = reverse('username_login')
            return HttpResponseRedirect(url)

        if request.user.is_authenticated():
            user = User.objects.get(username=request.user)
            url = reverse(redirect_map[user.type])
            return HttpResponseRedirect(url)
        return render(request, self.template_name, {'form': form, 'user': user, 'logo': logo})

    def post(self, request, *args, **kwargs):
        redirect_map = {
            'EMPLOYEE': 'dashboard',
            'ADMINISTRATOR': 'admin_dashboard'
        }

        username = request.GET.get('username')
        user = User.objects.filter(username__username=username).first()
        logo = Utility.objects.first()

        if user is None:
            url = reverse('username_login')
            return HttpResponseRedirect(url)

        form = self.form_class(request.POST)
        url = reverse(redirect_map[user.type])
        if form.is_valid():
            user = form.login(request)
            _login = login(request, user)
            return HttpResponseRedirect(url)
        return render(request, self.template_name, {'form': form, 'user':user, 'logo': logo})


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
            messages.success(request, 'Company has been created successfully!')
            return HttpResponseRedirect(url)
        else:
            messages.warning(request, 'Company already exists.')
            return HttpResponseRedirect(url)

        context['form'] = self.form_class()
        return render(request, self.template_name, context)


class ViewEmployee(AdministratorView):
    template_name = 'administrator/view_employee.html'
    form_class = SearchForm

    def get_employees(self, company_id, q=None):
        user = User.objects.filter(company__id=company_id)
        if q:
            user = user.filter(Q(first_name__icontains=q) | Q(middle_name__icontains=q) | Q(last_name__icontains=q) | Q(position__icontains=q))
        return user

    def get(self, request, company_id, *args, **kwargs):
        q = request.GET.get('q')
        context = self.get_context(request)
        context['company'] = Company.objects.get(id=company_id)
        context['employees'] = self.get_employees(company_id, q)
        context['search'] = self.form_class()
        return render(request, self.template_name, context)

    def post(self, request, company_id, *args, **kwargs):
        url = reverse('view_employee', kwargs={'company_id': company_id})
        form = self.form_class(request.POST or None)

        if form.is_valid():
            q = form.cleaned_data.get('q')
            return HttpResponseRedirect(url + '?q={}'.format(q))


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
            user.color = form.cleaned_data.get('color')
            user.save()
            messages.success(request, 'Text INFO to {} (Cross-telco: {}) to subscribe to SMS Notification.'.format(short_code, cross_telco))
            return HttpResponseRedirect(url)
        else:
            messages.warning(request, form.errors.values()[0][0])
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
    assign_form_class = AssignForm
    search_form_class = SearchForm

    def build_thread_array(self, count):
        thread = []
        for x in range(count):
            thread.append("")
        return thread

    def get_issue_directory(self, tracker_id, q=None):
        issues_directory = {}
        issues = Issue.objects.filter(tracker__id=tracker_id).filter(decision='OPEN').order_by('-id')

        if q:
            issues = issues.filter(Q(title__icontains=q) | Q(reference_id__icontains=q) | Q(priority__icontains=q))

        counter = 0
        for issue in issues:
            timestamp = timezone.localtime(issue.date_created).strftime("%m-%d-%Y %H:%M:%S")
            if timestamp not in issues_directory:
                thread = self.build_thread_array(issues.count())
                if issue.description:
                    thread[counter] = issue.description + "|" + issue.assigned_to.color
                    issues_directory[timestamp] = thread
            else:
                if issue.description:
                    issues_directory[timestamp][counter] = issue.description

            for note in issue.threads.all():
                timestamp = timezone.localtime(note.date_created).strftime("%m-%d-%Y %H:%M:%S")
                if timestamp not in issues_directory:
                    thread = self.build_thread_array(issues.count())
                    thread[counter] = note.callout + " - " + note.note + "|" + note.assigned_to.color
                    issues_directory[timestamp] = thread
                else:
                    issues_directory[timestamp][counter] = note.callout + " - " + note.note + "|" + note.assigned_to.color
            counter += 1

        return OrderedDict(sorted(issues_directory.items()))

    def get_issue(self, tracker_id, q=None):
        issue = Issue.objects.filter(tracker__id=tracker_id).filter(decision='OPEN').order_by('-id')
        if q:
            return issue.filter(Q(title__icontains=q) | Q(reference_id__icontains=q) | Q(priority__icontains=q))
        return issue

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
        q = request.GET.get('q')
        respond_form = self.respond_form_class(tracker_id)
        assign_form = self.assign_form_class(tracker_id)
        context = self.get_context(request)
        context['issues'] = self.get_issue(tracker_id, q)
        context['issue_directory'] = self.get_issue_directory(tracker_id, q)
        context['tracker'] = Tracker.objects.get(id=tracker_id)
        context['form'] = form
        context['search'] = self.search_form_class()
        context['respond_form'] = respond_form
        context['assign_form'] = assign_form
        context['active_tracker'] = tracker_id
        return render(request, self.template_name, context)

    def post(self, request, tracker_id, *args, **kwargs):
        url = reverse('admin_tracker_issue', kwargs={'tracker_id':tracker_id})
        form = self.form_class(request.POST or None)
        assign_form = self.assign_form_class(tracker_id, request.POST or None)
        respond_form = self.respond_form_class(tracker_id, request.POST or None)
        search_form = self.search_form_class(request.POST or None)
        context = self.get_context(request)
        context['issues'] = self.get_issue(tracker_id)
        context['issue_directory'] = self.get_issue_directory(tracker_id)
        context['respond_form'] = respond_form
        context['active_tracker'] = tracker_id
        context['assign_form'] = assign_form
        context['tracker'] = Tracker.objects.get(id=tracker_id)
        context['form'] = form

        if search_form.is_valid():
            q = search_form.cleaned_data.get('q')
            return HttpResponseRedirect(url + '?q={}'.format(q))

        if form.is_valid() and request.POST.get('issue_id') == None:
            data = form.cleaned_data
            data['tracker'] = Tracker.objects.get(id=tracker_id)
            data['created_by'] = User.objects.get(username=request.user)
            issue = Issue.objects.create(**data)
            return HttpResponseRedirect(url)

        if respond_form.is_valid():
            data = respond_form.cleaned_data
            issue = Issue.objects.get(id=data.get('issue_id'))
            user = User.objects.get(id=data.get('assigned_to'))
            issue.decision = data.get('decision')
            issue.save()
            thread = Thread(issue=issue,
                            assigned_to=user,
                            note=data.get('message'),
                            callout=data.get('callout'),
                            created_by=User.objects.get(username=request.user))
            thread.save()
            return HttpResponseRedirect(url)

        if assign_form.is_valid():
            data = assign_form.cleaned_data
            user = User.objects.get(id=data.get('assigned_to'))
            issue = Issue.objects.get(id=data.get('issue_id'))
            issue.priority = data.get('priority')
            issue.assigned_to = user
            issue.description = data.get('description')
            issue.date_created = timezone.now()
            issue.save()
            self.send_sms_notification(issue)
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
            user.color = form.cleaned_data.get('color')
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
        url = reverse('view_employee', kwargs={'company_id': request.GET.get('company_id')})
        user = AuthUser.objects.filter(auth_user__id=employee_id).first()
        user.delete()
        return HttpResponseRedirect(url)


class AdminDashboard(AdministratorView):
    template_name = 'administrator/dashboard.html'

    def build_statistics(self):
        statistics = OrderedDict()
        open = Issue.objects.filter(decision='OPEN').count()
        sleep = Issue.objects.filter(decision='SLEEP').count()
        closed = Issue.objects.filter(decision='CLOSED').count()
        dead = Issue.objects.filter(decision='DEAD').count()
        low = Issue.objects.filter(priority='LOW').count()
        normal = Issue.objects.filter(priority='NORMAL').count()
        high = Issue.objects.filter(priority='HIGH').count()

        statistics['open'] = open
        statistics['sleep'] = sleep
        statistics['closed'] = closed
        statistics['dead'] = dead
        statistics['low'] = low
        statistics['normal'] = normal
        statistics['high'] = high

        return statistics

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        context['statistics'] = self.build_statistics()
        return render(request, self.template_name, context)


class ArchiveView(AdministratorView):
    template_name = 'administrator/archive.html'
    form_class = DecisionForm
    search_form_class = SearchForm

    def get(self, request, *args, **kwargs):
        status = request.GET.get('status')
        q = request.GET.get('q')
        context = self.get_context(request)

        issue = Issue.objects.filter(Q(decision=status) | Q(priority=status))
        if q:
            issue = issue.filter(Q(title__icontains=q) | Q(tracker__name__icontains=q) | Q(tracker__company__name__icontains=q))

        context['status'] = status
        context['issues'] = issue
        context['form'] = self.form_class()
        context['search'] = self.search_form_class()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        url = reverse('archive')
        status = request.GET.get('status')

        form = self.form_class(request.POST or None)
        search_form = self.search_form_class(request.POST or None)

        if search_form.is_valid():
            q = search_form.cleaned_data.get('q')
            return HttpResponseRedirect(url + '?status={}&q={}'.format(status, q))

        if form.is_valid():
            data = form.cleaned_data
            issue = Issue.objects.get(id=data.get('issue_id'))
            issue.decision = data.get('decision')
            issue.priority = data.get('priority')
            issue.save()
            return HttpResponseRedirect(url + '?status={}'.format(status))


class AdminThreadView(AdministratorView):
    template_name = 'administrator/thread.html'
    form_class = IssueForm
    respond_form_class = RespondForm
    assign_form_class = AssignForm

    def build_thread_array(self, count):
        thread = []
        for x in range(count):
            thread.append("")
        return thread

    def get_issue_directory(self, issue_id):
        issues_directory = {}
        issues = Issue.objects.filter(id=issue_id)

        counter = 0
        for issue in issues:
            timestamp = timezone.localtime(issue.date_created).strftime("%m-%d-%Y %H:%M:%S")
            if timestamp not in issues_directory:
                thread = self.build_thread_array(issues.count())
                if issue.description:
                    thread[counter] = issue.description + "|" + issue.assigned_to.color
                    issues_directory[timestamp] = thread
            else:
                if issue.description:
                    issues_directory[timestamp][counter] = issue.description

            for note in issue.threads.all():
                timestamp = timezone.localtime(note.date_created).strftime("%m-%d-%Y %H:%M:%S")
                if timestamp not in issues_directory:
                    thread = self.build_thread_array(issues.count())
                    thread[counter] = note.callout + " - " + note.note + "|" + note.assigned_to.color
                    issues_directory[timestamp] = thread
                else:
                    issues_directory[timestamp][counter] = note.callout + " - " + note.note + "|" + note.assigned_to.color
            counter += 1

        return OrderedDict(sorted(issues_directory.items()))

    def get(self, request, issue_id, *args, **kwargs):
        context = self.get_context(request)
        issue = Issue.objects.get(id=issue_id)
        form = self.form_class()
        respond_form = self.respond_form_class(issue.tracker.id)
        assign_form = self.assign_form_class(issue.tracker.id)

        context['issues'] = Issue.objects.filter(id=issue_id)
        context['issue_directory'] = self.get_issue_directory(issue_id)

        context['form'] = form
        context['respond_form'] = respond_form
        context['assign_form'] = assign_form
        return render(request, self.template_name, context)

    def post(self, request, issue_id, *args, **kwargs):
        url = reverse('admin_issue_thread', kwargs={'issue_id':issue_id})
        issue = Issue.objects.get(id=issue_id)

        assign_form = self.assign_form_class(issue.tracker.id, request.POST or None)
        respond_form = self.respond_form_class(issue.tracker.id, request.POST or None)

        context = self.get_context(request)

        if respond_form.is_valid():
            data = respond_form.cleaned_data
            issue = Issue.objects.get(id=data.get('issue_id'))
            user = User.objects.get(id=data.get('assigned_to'))
            issue.decision = data.get('decision')
            issue.save()
            thread = Thread(issue=issue,
                            assigned_to=user,
                            note=data.get('message'),
                            callout=data.get('callout'),
                            created_by=User.objects.get(username=request.user))
            thread.save()
            return HttpResponseRedirect(url)

        if assign_form.is_valid():
            data = assign_form.cleaned_data
            user = User.objects.get(id=data.get('assigned_to'))
            issue = Issue.objects.get(id=data.get('issue_id'))
            issue.priority = data.get('priority')
            issue.assigned_to = user
            issue.description = data.get('description')
            issue.date_created = timezone.now()
            issue.save()
            return HttpResponseRedirect(url)

        return render(request, self.template_name, context)

class AdministratorSettings(AdministratorView):
    template_name = 'administrator/settings.html'
    account_form_class = ChangePasswordForm
    update_form_class = UpdateUserForm
    logo_form_class = LogoForm

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        user = User.objects.get(username=self.request.user)
        logo = Utility.objects.first()
        context['account_form'] = self.account_form_class()
        context['update_form'] = self.update_form_class(instance=user)
        context['logo_form'] = self.logo_form_class(instance=logo)
        context['logo'] = logo
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        url = reverse('settings')
        context = self.get_context(request)
        user = User.objects.get(username=self.request.user)
        logo = Utility.objects.first()
        account_form = self.account_form_class(request.POST or None)
        logo_form = self.logo_form_class(request.POST or None, request.FILES or None, instance=logo)
        update_form = self.update_form_class(request.POST or None, request.FILES or None, instance=user)
        context['account_form'] = account_form
        context['update_form'] = update_form
        context['logo_form'] = logo_form
        context['logo'] = logo

        if account_form.is_valid():
            data = account_form.cleaned_data
            user = authenticate(username=self.request.user.username, password=data.get('old_password'))

            if user is not None:
                user.set_password(data.get('new_password'))
                user.save()
                return HttpResponseRedirect(url)
            else:
                messages.warning(request, 'Password change was unsuccessful!')
                return HttpResponseRedirect(url)

        if update_form.is_valid():
            data = update_form.cleaned_data
            user = User.objects.get(username=self.request.user)
            user.first_name = data.get('first_name')
            user.middle_name = data.get('middle_name')
            user.last_name = data.get('last_name')
            user.sex = data.get('sex')
            user.date_of_birth = data.get('date_of_birth')
            user.mobile_number = data.get('mobile_number')
            user.company = data.get('company')
            user.position = data.get('position')
            user.picture = data.get('picture')
            user.color = data.get('color')
            user.save()
            messages.success(request, 'Profile has been updated successfully.')
            return HttpResponseRedirect(url)

        if logo_form.is_valid():
            data = logo_form.cleaned_data
            if logo is not None:
                logo.logo = data.get('logo')
            else:
                logo = Utility(logo=data.get('logo'))
            logo.save()
            messages.success(request, 'The logo has been updated successfully.')
            return HttpResponseRedirect(url)

        else:
            messages.warning(request, 'Update is not successful!')
            return HttpResponseRedirect(url)

        return render(request, self.template_name, context)


# EMPLOYEE VIEWS: MUST REFACTOR THESE TWO MODES

class EmployeeView(HasRoleMixin, TemplateView):
    allowed_roles = [Employee,]

    def get_user(self, request):
        return  User.objects.filter(username=request.user).first()

    def get_notification(self, request):
        return Notification.objects.filter(user__username=request.user).order_by('-id')

    def get_trackers(self, request):
        user = User.objects.filter(username=request.user).first()
        return Tracker.objects.filter(company=user.company)

    def get_context(self, request):
        context = {}
        context['user'] = self.get_user(request)
        context['notifications'] = self.get_notification(request)
        context['unread'] = context['notifications'].filter(read=False)
        context['trackers'] = self.get_trackers(request)
        return context


class DashboardView(EmployeeView):
    template_name = 'user/index.html'

    def build_statistics(self, request):
        statistics = OrderedDict()
        user = User.objects.get(username=request.user)
        issue = Issue.objects.filter(tracker__company=user.company)
        open = issue.filter(decision='OPEN').count()
        sleep = issue.filter(decision='SLEEP').count()
        closed = issue.filter(decision='CLOSED').count()
        dead = issue.filter(decision='DEAD').count()
        low = issue.filter(priority='LOW').count()
        normal = issue.filter(priority='NORMAL').count()
        high = issue.filter(priority='HIGH').count()

        statistics['open'] = open
        statistics['sleep'] = sleep
        statistics['closed'] = closed
        statistics['dead'] = dead
        statistics['low'] = low
        statistics['normal'] = normal
        statistics['high'] = high

        return statistics

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        context['statistics'] = self.build_statistics(request)
        return render(request, self.template_name, context)


class IssueView(EmployeeView):
    template_name = 'user/issue.html'
    form_class = EmployeeRespondForm
    search_form_class = SearchForm

    def build_thread_array(self, count):
        thread = []
        for x in range(count):
            thread.append("")
        return thread

    def get_issue_directory(self, tracker_id, q=None):
        issues_directory = {}
        issues = Issue.objects.filter(tracker__id=tracker_id).filter(decision='OPEN').order_by('-id')

        if q:
            issues = issues.filter(Q(title__icontains=q) | Q(reference_id__icontains=q) | Q(priority__icontains=q))

        counter = 0
        for issue in issues:
            timestamp = timezone.localtime(issue.date_created).strftime("%m-%d-%Y %H:%M:%S")
            if timestamp not in issues_directory:
                thread = self.build_thread_array(issues.count())
                if issue.description:
                    thread[counter] = issue.description + "|" + issue.assigned_to.color
                    issues_directory[timestamp] = thread
            else:
                if issue.description:
                    issues_directory[timestamp][counter] = issue.description

            for note in issue.threads.all():
                timestamp = timezone.localtime(note.date_created).strftime("%m-%d-%Y %H:%M:%S")
                if timestamp not in issues_directory:
                    thread = self.build_thread_array(issues.count())
                    thread[counter] = note.callout + " - " + note.note + "|" + note.assigned_to.color
                    issues_directory[timestamp] = thread
                else:
                    issues_directory[timestamp][counter] = note.callout + " - " + note.note + "|" + note.assigned_to.color
            counter += 1

        return OrderedDict(sorted(issues_directory.items()))

    def get_issue(self, tracker_id, q=None):
        issue = Issue.objects.filter(tracker__id=tracker_id).filter(decision='OPEN').order_by('-id')
        if q:
            return issue.filter(Q(title__icontains=q) | Q(reference_id__icontains=q) | Q(priority__icontains=q))
        return issue

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
        form = self.form_class(tracker_id)
        q = request.GET.get('q')
        context = self.get_context(request)
        context['issues'] = self.get_issue(tracker_id, q)
        context['issue_directory'] = self.get_issue_directory(tracker_id, q)
        context['tracker'] = Tracker.objects.get(id=tracker_id)
        context['respond_form'] = form
        context['search'] = self.search_form_class()

        return render(request, self.template_name, context)

    def post(self, request, tracker_id, *args, **kwargs):
        url = reverse('issue', kwargs={'tracker_id': tracker_id})
        form = self.form_class(tracker_id, request.POST or None)
        search_form = self.search_form_class(request.POST or None)

        if search_form.is_valid():
            q = search_form.cleaned_data.get('q')
            return HttpResponseRedirect(url + '?q={}'.format(q))

        if form.is_valid():
            data = form.cleaned_data
            issue = Issue.objects.get(id=data.get('issue_id'))
            user = User.objects.get(id=data.get('assigned_to'))
            thread = Thread(issue=issue,
                            assigned_to=user,
                            note=data.get('message'),
                            callout=data.get('callout'),
                            created_by=User.objects.get(username=request.user))
            thread.save()
            return HttpResponseRedirect(url)


class EmployeeArchiveView(EmployeeView):
    template_name = 'user/archive.html'
    search_form_class = SearchForm

    def get(self, request, *args, **kwargs):
        status = request.GET.get('status')
        q = request.GET.get('q')

        context = self.get_context(request)
        context['status'] = status

        user = User.objects.get(username=request.user)
        issue = Issue.objects.filter(tracker__company=user.company)
        issue = issue.filter(Q(decision=status) | Q(priority=status))

        if q:
            issue = issue.filter(Q(title__icontains=q) | Q(tracker__name__icontains=q))

        context['issues'] = issue
        context['search'] = self.search_form_class()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.search_form_class(request.POST or None)
        status = request.GET.get('status')
        url = reverse('archive_employee')

        if form.is_valid():
            q = form.cleaned_data.get('q')
            return HttpResponseRedirect(url + '?status={}&q={}'.format(status, q))
        return HttpResponseRedirect(url + '?status={}'.format(status))

class EmployeeSettings(EmployeeView):
    template_name = 'user/settings.html'
    account_form_class = ChangePasswordForm
    update_form_class = UpdateUserForm

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        user = User.objects.get(username=self.request.user)
        context['account_form'] = self.account_form_class()
        context['update_form'] = self.update_form_class(instance=user)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        url = reverse('employee_settings')
        context = self.get_context(request)
        user = User.objects.get(username=self.request.user)
        logo = Utility.objects.first()
        account_form = self.account_form_class(request.POST or None)
        update_form = self.update_form_class(request.POST or None, request.FILES or None, instance=user)
        context['account_form'] = account_form
        context['update_form'] = update_form

        if account_form.is_valid():
            data = account_form.cleaned_data
            user = authenticate(username=self.request.user.username, password=data.get('old_password'))

            if user is not None:
                user.set_password(data.get('new_password'))
                user.save()
                return HttpResponseRedirect(url)
            else:
                messages.warning(request, 'Password change was unsuccessful!')
                return HttpResponseRedirect(url)

        if update_form.is_valid():
            data = update_form.cleaned_data
            user = User.objects.get(username=self.request.user)
            user.first_name = data.get('first_name')
            user.middle_name = data.get('middle_name')
            user.last_name = data.get('last_name')
            user.sex = data.get('sex')
            user.date_of_birth = data.get('date_of_birth')
            user.mobile_number = data.get('mobile_number')
            user.company = data.get('company')
            user.position = data.get('position')
            user.picture = data.get('picture')
            user.color = data.get('color')
            user.save()
            messages.success(request, 'Profile has been updated successfully.')
            return HttpResponseRedirect(url)

        else:
            messages.warning(request, 'Update is unsuccessful.')
            return HttpResponseRedirect(url)

@method_decorator(csrf_exempt, name='dispatch')
class SMSView(View):
    def get(self, request, *args, **kwargs):
        access_token = self.request.GET.get('access_token')
        subscriber_number = self.request.GET.get('subscriber_number')

        print(self.request.GET)

        User.objects.filter(mobile_number__endswith=subscriber_number).update(access_token=access_token)
        return HttpResponse()

    def post(self, request, *args, **kwargs):
        unsubscribed = json.loads(self.request.body).get('unsubscribed')

        print(self.request.body)

        User.objects.filter(mobile_number__endswith=unsubscribed.get('subscriber_number')).update(access_token=None)
        return HttpResponse()
