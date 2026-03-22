from django.test import TestCase
from BetaTrax.models import Employee, Product, Report

class ProductOwnerTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Test Product')
        self.employee = Employee.objects.create_user(
            email='test@test.com',
            password='testpassword',
            role='PRODUCT_OWNER',
            product=self.product,
        )
    def test_submit_and_view_report(self):
        self.assertEqual(self.client.post('/report/', {
            'title': 'Report 1',
            'description': 'Description 1',
            'reproduce_steps': 'Reproduce steps 1',
            'product': self.product.id,
        }).status_code, 200)
        self.assertEqual(self.client.post('/report/', {
            'title': 'Report 2',
            'description': 'Description 2',
            'reproduce_steps': 'Reproduce steps 2',
            'product': self.product.id,
            'tester_email': 'tester@test.com',
        }).status_code, 200)
        self.assertEqual(self.client.get('/report/').status_code, 302)
        self.assertEqual(self.client.post('/login/', {
            'email': self.employee.email,
            'password': 'testpassword',
        }).status_code, 200)
        self.assertEqual(self.client.get('/report/').status_code, 200)
        self.assertEqual(self.client.get('/report/?status=NEW').status_code, 200)
        self.assertEqual(self.client.get('/report/?status=CANNOT_REPRODUCE&page=1&sort=-priority').status_code, 200)
        self.assertEqual(self.client.get('/report/?status=OPEN&page=2&sort=UwU').status_code, 400)
        self.assertEqual(self.client.get('/report/?status=KALTSIT&page=2&sort=-priority').status_code, 400)
        self.assertEqual(self.client.get('/report/?status=OPEN&page=p&sort=-priority').status_code, 400)
        self.assertEqual(self.client.get('/report/?status=OPEN&page=2&sort=-priority').status_code, 400)