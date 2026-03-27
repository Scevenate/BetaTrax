from django.test import TestCase
from BetaTrax.models import Product, Employee

class TestCrud(TestCase):
    def test_actions(self):
        self.product = Product.objects.create(name='Ice cream')
        self.owner = Employee.objects.create_user(
            email='owner@icecream.com',
            password='ownerpassword',
            role='PRODUCT_OWNER',
            product=self.product.id,
        )
        self.developer = Employee.objects.create_user(
            email='developer@icecream.com',
            password='developerpassword',
            role='DEVELOPER',
            product=self.product.id,
        )
        reports = [{
            'title': 'Report 1',
            'description': 'Description 1',
            'reproduce_steps': 'Reproduce steps 1',
            'product': self.product.id,
            'tester_id': 'tester 1',
        }, {
            'title': 'Report 2',
            'description': 'Description 2',
            'reproduce_steps': 'Reproduce steps 2',
            'product': self.product.id,
            'tester_id': 'tester 2',
            'tester_email': 'tester2@test.com',
        }, {
            'title': 'Report 3',
            'description': 'Description 3',
            'reproduce_steps': 'Reproduce steps 3',
            'product': self.product.id,
            'tester_id': 'tester 3',
            'tester_email': 'tester3@test.com',
        }]
        self.assertEqual(self.client.post('/report/', reports[0]).status_code, 201)
        self.assertEqual(self.client.post('/report/', reports[1]).status_code, 201)
        self.assertEqual(self.client.post('/report/', reports[2]).status_code, 201)
        self.assertEqual(self.client.post('/login/', {
            'email': self.owner.email,
            'password': 'ownerpassword',
        }).status_code, 200)
        self.assertEqual(self.client.patch('/report/1/', {
            'action': 'OPEN',
            'severity': 2,
            'priority': 2,
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.patch('/report/3/', {
            'action': 'OPEN',
            'severity': 3,
            'priority': 0,
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.patch('/report/1/', {
            'action': 'ASSIGN',
        }, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.post('/login/', {
            'email': self.developer.email,
            'password': 'developerpassword',
        }).status_code, 403)
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.patch('/report/2/', {
            'action': 'DUPLICATE',
            'duplicate_of': 1,
        }, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.post('/login/', {
            'email': self.developer.email,
            'password': 'developerpassword',
        }).status_code, 200)
        self.assertEqual(self.client.patch('/report/1/', {
            'action': 'ASSIGN',
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.patch('/report/3/', {
            'action': 'ASSIGN',
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.patch('/report/2/', {
            'action': 'DUPLICATE',
            'duplicate_of': 1,
        }, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.patch('/report/1/', {
            'action': 'FIX',
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.patch('/report/3/', {
            'action': 'FIX',
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': self.owner.email,
            'password': 'ownerpassword',
        }).status_code, 200)
        self.assertEqual(self.client.patch('/report/2/', {
            'action': 'DUPLICATE',
            'duplicate_of': 1,
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.patch('/report/1/', {
            'action': 'REOPEN',
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.patch('/report/3/', {
            'action': 'RESOLVE',
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': self.developer.email,
            'password': 'developerpassword',
        }).status_code, 200)
        self.assertEqual(self.client.patch('/report/1/', {
            'action': 'FIX',
        }, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.patch('/report/1/', {
            'action': 'RESOLVE',
        }, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.patch('/report/1/', {
            'action': 'ASSIGN',
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.patch('/report/1/', {
            'action': 'FIX',
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.post('/logout/').status_code, 200)