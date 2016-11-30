from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from . forms import *


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
            print('=============')
            print(_login)
            return HttpResponseRedirect('/')
        return render(request, self.template_name, {'form': form})
