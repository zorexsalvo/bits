import time
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import View
from .forms import *
from .models import Company, User


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/')


class LoginView(TemplateView):
    form_class = LoginForm
    template_name = 'security/login.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
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

    form_class = CreateCompanyForm
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
        form = self.form_class(request.POST or None)
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
            user.company = Company.objects.filter(pk=form.cleaned_data.get('company')).first()
            user.position = form.cleaned_data.get('position')
            user.save()
            context['form'] = self.form_class()
            return render(request, self.template_name, context)

        context['form'] = form
        return render(request, self.template_name, context)
