import time
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import View

from .forms import *
from .models import Company, User, Tracker


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/')


class LoginView(TemplateView):
    form_class = LoginForm
    template_name = 'security/login.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        if request.user.is_authenticated():
            return HttpResponseRedirect('/create_company')
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.login(request)
            _login = login(request, user)
            return HttpResponseRedirect('/create_company/')
        return render(request, self.template_name, {'form': form})


class AdministratorView(TemplateView):
    def get_companies(self):
        return Company.objects.all()

    def get_user(self, request):
        return  User.objects.filter(username=request.user).first()

    def get_context(self, request):
        context = {}
        context['companies'] = self.get_companies()
        context['user'] = self.get_user(request)
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
        context = self.get_context(request)
        form = self.form_class(request.POST or None)
        context['request'] = 'POST'

        if form.is_valid():
            name = form.cleaned_data.get('name')
            company = Company(name=name)
            company.save()
            context['form'] = self.form_class()
            return render(request, self.template_name, context)

        context['form'] = form
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
        context = self.get_context(request)
        form = self.form_class(request.POST, request.FILES)
        context['request'] = 'POST'

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
            context['form'] = self.form_class()
            return render(request, self.template_name, context)
        context['form'] = form
        return render(request, self.template_name, context)


class CreateTracker(AdministratorView):
    template_name = 'administrator/create_tracker.html'
    form_class = TrackerForm

    def get(self, request, company_id, *args, **kwargs):
        context = self.get_context(request)
        context['form'] = self.form_class()
        return render(request, self.template_name, context)

    def post(self, request, company_id, *args, **kwargs):
        context = self.get_context(request)
        form = self.form_class(request.POST or None)
        context['request'] = 'POST'

        if form.is_valid():
            tracker = Tracker.objects.create(name=form.cleaned_data.get('tracker'),
                                             company=Company.objects.get(id=company_id))
            context['form'] = self.form_class()
            return render(request, self.template_name, context)

        context['form'] = form
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
        form = self.form_class(request.POST, request.FILES)
        context = self.get_context(request)
        context['request'] = 'POST'

        if form.is_valid():
            user = User.objects.filter(id=employee_id)
            user.update(
                first_name = form.cleaned_data.get('first_name'),
                middle_name = form.cleaned_data.get('middle_name'),
                last_name = form.cleaned_data.get('last_name'),
                sex = form.cleaned_data.get('sex'),
                date_of_birth = form.cleaned_data.get('date_of_birth'),
                mobile_number = form.cleaned_data.get('mobile_number'),
                company = form.cleaned_data.get('company'),
                position = form.cleaned_data.get('position'),
                picture = form.cleaned_data.get('picture')
            )
            context['form'] = form
            return render(request, self.template_name, context)

        context['form'] = form
        return render(request, self.template_name, context)


class DeleteEmployee(AdministratorView):
    def get(self, request, employee_id, *args, **kwargs):
        user = User.objects.filter(id=employee_id)
        user.delete()
        return HttpResponseRedirect('/view_employee')


class UserView(TemplateView):
    def get_user(self, request):
        return  User.objects.filter(username=request.user).first()

    def get_context(self, request):
        context = {}
        context['user'] = self.get_user(request)
        return context


class DashboardView(UserView):
    template_name = 'user/index.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        return render(request, self.template_name, context)


class IssueView(UserView):
    template_name = 'user/issue.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        return render(request, self.template_name, context)


class UserDirectoryView(UserView):
    template_name = 'user/user.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        return render(request, self.template_name, context)


class CheckView(UserView):
    template_name = 'user/check.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context(request)
        return render(request, self.template_name, context)
