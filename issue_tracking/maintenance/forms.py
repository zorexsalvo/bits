from datetime import date
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import *


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username','class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            raise forms.ValidationError('Invalid credentials.')
        return self.cleaned_data

    def login(self, request):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        return user

    class Meta:
        model = User
        fields = ['username', 'password']


class CreateCompanyForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter company name', 'class': 'form-control'}))

    def clean(self):
        data = self.cleaned_data['name']
        if Company.objects.filter(name=data):
            raise forms.ValidationError('Company already exists.')
        return self.cleaned_data


class UserForm(forms.Form):
    SEX = (('MALE', 'Male',), ('FEMALE', 'Female',))
    COMPANY = ()
    COMPANY += tuple((company.id, company.name) for company in Company.objects.all())
    TYPE = (('ADMIN', 'Admin'),
            ('EMPLOYEE', 'Employee'))

    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}))
    middle_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Middle Name', 'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control pull-right', 'id': 'datepicker'}))
    sex = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=SEX)
    mobile_number = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Mobile Number', 'class': 'form-control'}))
    company = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=COMPANY)
    position = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Position', 'class': 'form-control'}))
    type = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=TYPE)
