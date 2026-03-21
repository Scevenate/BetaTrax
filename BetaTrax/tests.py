from django.test import TestCase
from .models import Employee, Product, Report

class EmployeeTestCase(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(
            email='test@test.com',
            password='testpassword',
            role='PRODUCT_OWNER',
            product=Product.objects.create(name='Test Product'),
        )