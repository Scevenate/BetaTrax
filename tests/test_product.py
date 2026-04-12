from django.test import TestCase
from BetaTrax.models import Product, Employee

class TestProduct(TestCase):
    def test_product(self):
        PO1 = Employee.objects.create_user(
            email='po@test.com',
            password='popassword',
            role='PRODUCT_OWNER',
        )
        PO2 = Employee.objects.create_user(
            email='po2@test.com',
            password='popassword2',
            role='PRODUCT_OWNER',
        )
        DEV1 = Employee.objects.create_user(
            email='dev1@test.com',
            password='devpassword',
            role='DEVELOPER',
        )
        self.assertEqual(self.client.post('/product/', {
            'name': 'Test Product',
        }).status_code, 403)
        self.assertEqual(self.client.patch('/employee/1/', {
            'product': 2,
        }, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.post('/login/', {
            'email': PO1.email,
            'password': 'popassword',
        }).status_code, 200)
        self.assertEqual(self.client.post('/product/', {
            'name': 'Test Product 1',
        }).status_code, 201)
        self.assertEqual(self.client.post('/product/', {
            'name': 'Test Product 2',
        }).status_code, 201)
        self.assertEqual(self.client.post('/product/', {
            'name': 'Test Product 3',
        }).status_code, 201)

        # additional dev test
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': DEV1.email,
            'password': 'devpassword',
        }).status_code, 200)
        self.assertEqual(self.client.post('/product/', {
            'name': 'Test Product 4',
        }).status_code, 403)
        self.assertEqual(self.client.patch('/employee/3/', {
            'product': 1,
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.get('/employee/3/').json()['product'], 1)
        self.assertEqual(Product.objects.get(id=1).has_owner, False)
        self.assertEqual(self.client.patch('/employee/3/', {
            'product': 2,
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.get('/employee/3/').json()['product'], 2)
        self.assertEqual(Product.objects.get(id=2).has_owner, False)
        self.assertEqual(self.client.patch('/employee/3/', {
            'product': 3,
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.get('/employee/3/').json()['product'], 3)
        self.assertEqual(Product.objects.get(id=3).has_owner, False)
        self.assertEqual(self.client.post('/logout/').status_code, 200)

        # continued PO test
        self.assertEqual(self.client.post('/login/', {
            'email': PO1.email,
            'password': 'popassword',
        }).status_code, 200)
        self.assertEqual(self.client.get('/employee/1/').json()['product'], None)
        self.assertEqual(self.client.patch('/employee/1/', {
            'product': 1,
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.get('/employee/1/').json()['product'], 1)
        self.assertEqual(Product.objects.get(id=1).has_owner, True)
        self.assertEqual(self.client.patch('/employee/1/', {
            'product': 2,
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.get('/employee/1/').json()['product'], 2)
        self.assertEqual(Product.objects.get(id=1).has_owner, False)
        self.assertEqual(Product.objects.get(id=2).has_owner, True)
        self.assertEqual(self.client.patch('/employee/2/', {
            'product': 1,
        }, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.get('/employee/2/').json()['product'], None)
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': PO2.email,
            'password': 'popassword2',
        }).status_code, 200)
        self.assertEqual(self.client.patch('/employee/2/', {
            'product': 2,
        }, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.get('/employee/2/').json()['product'], None)
        self.assertEqual(self.client.patch('/employee/2/', {
            'product': 3,
        }, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.get('/employee/2/').json()['product'], 3)
        self.assertEqual(Product.objects.get(id=2).has_owner, True)
        self.assertEqual(Product.objects.get(id=3).has_owner, True)
        self.assertEqual(self.client.post('/logout/').status_code, 200)