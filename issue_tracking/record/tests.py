from django.test import TestCase, Client

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse

from .models import Company, Tracker, Issue
from .forms import LoginForm, CompanyForm, IssueForm

class ModelTestCase(TestCase):
    def setUp(self):
        pass

    def test_create_company(self):
        company = Company(name='My Company')
        company.save()


class LoginTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='juan',
                                        password='password123',
                                        email='juan@bits.com')

    def test_login(self):
        form = LoginForm({'username': 'juan', 'password': 'password123'})

        self.assertTrue(form.is_valid())
        self.assertIsNotNone(authenticate(username='juan', password='password123'))


class CompanyTestCase(TestCase):
    def setUp(self):
        client = Client()

        user = User.objects.create_user(username='juan',
                                        password='password123',
                                        email='juan@bits.com')

    def test_save_company_unauthenticated(self):
        url = reverse('create_company')
        form = CompanyForm({'name': 'Ayannah'})

        self.assertTrue(form.is_valid())
        response = self.client.post(url, form=form)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/create_company/')

    def test_save_company_authenticated(self):
        self.client.login(username='juan', password='password123')

        url = reverse('create_company')
        form = CompanyForm({'name': 'Ayannah'})

        self.assertTrue(form.is_valid())
        response = self.client.post(url, data=form.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Company.objects.count(), 1)


class TrackerTestCase(TestCase):
    def setUp(self):
        company = Company(name='My Company')
        company.save()

    def test_save_tracker(self):
        company = Company.objects.filter(name='My Company').first()
        tracker = Tracker(name='Tracker1',
                          company=company)
        tracker.save()

        self.assertIsNotNone(company)
        self.assertEqual(Tracker.objects.count(), 1)


class IssueTestCase(TestCase):
    def setUp(self):
        pass

    def test_save_issue(self):
        issue_form = IssueForm({'title': 'Test this bug!',
                                'created_by': 'unittest'})
        self.assertTrue(issue_form.is_valid)

        issue_form.save()
        self.assertEqual(1, Issue.objects.count())
