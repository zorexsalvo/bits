from datetime import date
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User as AuthUser
from django.db.models import Q
from .models import *


class UsernameForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'username', 'class': 'form-control'}))

    def clean(self):
        if not User.objects.filter(username__username=self.cleaned_data.get('username')):
            raise forms.ValidationError('No such user.')
        return self.cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'username','class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password', 'class': 'form-control'}))

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
        model = AuthUser
        fields = ['username', 'password']


class CompanyForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter company name', 'class': 'form-control'}))

    def clean(self):
        data = self.cleaned_data['name']
        if Company.objects.filter(name=data):
            raise forms.ValidationError('Company already exists.')
        return self.cleaned_data


class UserForm(forms.Form):
    SEX = (('MALE', 'Male',), ('FEMALE', 'Female',))
    TYPE = (('ADMINISTRATOR', 'Admin'),
            ('EMPLOYEE', 'Employee'))

    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}))
    middle_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Middle Name', 'class': 'form-control'}), required=False)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control pull-right', 'id': 'datepicker'}))
    sex = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=SEX)
    mobile_number = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Mobile Number', 'class': 'form-control'}))
    company = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), queryset=Company.objects.all())
    position = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Position', 'class': 'form-control'}))
    picture = forms.ImageField()
    type = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=TYPE)

    def clean(self):
        if AuthUser.objects.filter(username=self.cleaned_data['username']):
            raise forms.ValidationError('Username already taken.')
        if User.objects.filter(first_name=self.cleaned_data['first_name']) \
                       .filter(middle_name=self.cleaned_data['middle_name']) \
                       .filter(last_name=self.cleaned_data['last_name']):
            raise forms.ValidationError('User already exists.')
        return self.cleaned_data


class UpdateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'
        exclude = ['username', 'created_by', 'type']
        widgets = {
            'username': forms.HiddenInput(),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'placeholder': 'Middle Name', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'placeholder': 'Mobile Number', 'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control pull right', 'id': 'datepicker'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'placeholder': 'Position', 'class': 'form-control'})
        }

class TrackerForm(forms.ModelForm):
    class Meta:
        model = Tracker
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Tracker Name', 'class': 'form-control'}),
            'company': forms.HiddenInput()
        }


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ('title',)
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Title', 'class': 'form-control'})
        }

class AssignForm(forms.Form):
    issue_id = forms.IntegerField(widget=forms.HiddenInput(attrs={'class': 'form-control', 'id': 'issue_id'}))
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'title', 'readonly': ''}))
    assigned_to = forms.ChoiceField(widget=forms.Select(attrs={'class':'form-control'}))
    priority = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control', 'id': 'priority'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))

    def __init__(self, tracker_id, *args, **kwargs):
        priority = (('LOW', 'Low'),
                    ('NORMAL', 'Normal'),
                    ('HIGH', 'High'))
        company = Tracker.objects.get(id=tracker_id).company
        choices = tuple([(x.id, str(x)) for x in User.objects.filter(Q(company=company) | Q(type='ADMINISTRATOR'))])
        super(AssignForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].choices = choices
        self.fields['priority'].choices = priority

class RespondForm(forms.Form):
    issue_id = forms.IntegerField(widget=forms.HiddenInput(attrs={'class': 'form-control', 'id': 'issue_id'}))
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'title', 'readonly': ''}))
    description = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id':'description', 'readonly': ''}))
    assigned_to = forms.ChoiceField(widget=forms.Select(attrs={'class':'form-control'}))
    decision = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))

    def __init__(self, tracker_id, *args, **kwargs):
        decision = (('OPEN', 'Open'),
                    ('CLOSED', 'Closed'),
                    ('SLEEP', 'Sleep'),
                    ('DEAD', 'Dead'))
        company = Tracker.objects.get(id=tracker_id).company
        choices = tuple([(x.id, str(x)) for x in User.objects.filter(Q(company=company) | Q(type='ADMINISTRATOR'))])
        super(RespondForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].choices = choices
        self.fields['decision'].choices = decision


class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['note',]
        widgets = {
            'note': forms.TextInput(attrs={'placeholder': 'Type message...', 'class': 'form-control'}),
        }


class CheckForm(forms.Form):
    keyword = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Please input the Reference ID of the issue you want to check.', 'class': 'form-control'}))
