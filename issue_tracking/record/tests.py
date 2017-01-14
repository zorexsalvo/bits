from django.test import TestCase
from .models import Company

class ModelTestCase(TestCase):
    def setUp(self):
        pass

    def test_create_company(self):
        company = Company(name='My Company')
        company.save()

