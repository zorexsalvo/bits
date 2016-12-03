import time
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


class CreateCompany(AdministratorView):

    form_class = CreateCompanyForm
    template_name = 'administrator/create_company.html'

    def get(self, request, *args, **kwargs):
        context = {}
        form = self.form_class()
        context['form'] = form
        context['companies'] = self.get_companies()
        context['user'] = self.get_user(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}
        form = self.form_class(request.POST or None)
        context['request'] = 'POST'
        context['companies'] = self.get_companies()
        context['user'] = self.get_user(request)

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
        context = {}
        context['companies'] = self.get_companies()
        context['employees'] = self.get_employees()
        context['user'] = self.get_user(request)
        return render(request, self.template_name, context)


class CreateEmployee(AdministratorView):
    template_name = 'administrator/create_employee.html'
    form_class = UserForm

    def get(self, request, *args, **kwargs):
        context = {}
        context['form'] = self.form_class()
        context['user'] = self.get_user(request)
        return render(request, self.template_name, context)
