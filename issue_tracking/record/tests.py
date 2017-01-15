from django.test import TestCase, Client

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse

from .models import Company
from .forms import LoginForm, CompanyForm

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

