from rest_framework.test import APITestCase, APIClient
from BetaTrax.models import Product, Employee
from django_tenants.test.cases import TenantTestCase

class TestProduct(APITestCase, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient(HTTP_HOST='tenant.test.com')

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
        self.assertEqual(self.client.patch(f'/employee/{PO1.id}/', {
            'product': 2,
        }).status_code, 403)
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
        product_1 = Product.objects.get(name='Test Product 1')
        product_2 = Product.objects.get(name='Test Product 2')
        product_3 = Product.objects.get(name='Test Product 3')

        # additional dev test
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': DEV1.email,
            'password': 'devpassword',
        }).status_code, 200)
        self.assertEqual(self.client.post('/product/', {
            'name': 'Test Product 4',
        }).status_code, 403)
        self.assertEqual(self.client.patch(f'/employee/{DEV1.id}/', {
            'product': product_1.id,
        }).status_code, 200)
        self.assertEqual(self.client.get(f'/employee/{DEV1.id}/').json()['product'], product_1.id)
        self.assertEqual(Product.objects.get(id=product_1.id).has_owner, False)
        self.assertEqual(self.client.patch(f'/employee/{DEV1.id}/', {
            'product': product_2.id,
        }).status_code, 200)
        self.assertEqual(self.client.get(f'/employee/{DEV1.id}/').json()['product'], product_2.id)
        self.assertEqual(Product.objects.get(id=product_2.id).has_owner, False)
        self.assertEqual(self.client.patch(f'/employee/{DEV1.id}/', {
            'product': product_3.id,
        }).status_code, 200)
        self.assertEqual(self.client.get(f'/employee/{DEV1.id}/').json()['product'], product_3.id)
        self.assertEqual(Product.objects.get(id=product_3.id).has_owner, False)
        self.assertEqual(self.client.post('/logout/').status_code, 200)

        # continued PO test
        self.assertEqual(self.client.post('/login/', {
            'email': PO1.email,
            'password': 'popassword',
        }).status_code, 200)
        self.assertEqual(self.client.get(f'/employee/{PO1.id}/').json()['product'], None)
        self.assertEqual(self.client.patch(f'/employee/{PO1.id}/', {
            'product': product_1.id,
        }).status_code, 200)
        self.assertEqual(self.client.get(f'/employee/{PO1.id}/').json()['product'], product_1.id)
        self.assertEqual(Product.objects.get(id=product_1.id).has_owner, True)
        self.assertEqual(self.client.patch(f'/employee/{PO1.id}/', {
            'product': product_2.id,
        }).status_code, 200)
        self.assertEqual(self.client.get(f'/employee/{PO1.id}/').json()['product'], product_2.id)
        self.assertEqual(Product.objects.get(id=product_1.id).has_owner, False)
        self.assertEqual(Product.objects.get(id=product_2.id).has_owner, True)
        self.assertEqual(self.client.patch(f'/employee/{PO2.id}/', {
            'product': product_1.id,
        }).status_code, 403)
        self.assertEqual(self.client.get(f'/employee/{PO2.id}/').json()['product'], None)
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': PO2.email,
            'password': 'popassword2',
        }).status_code, 200)
        self.assertEqual(self.client.patch(f'/employee/{PO2.id}/', {
            'product': product_2.id,
        }).status_code, 400)
        self.assertEqual(self.client.get(f'/employee/{PO2.id}/').json()['product'], None)
        self.assertEqual(self.client.patch(f'/employee/{PO2.id}/', {
            'product': product_3.id,
        }).status_code, 200)
        self.assertEqual(self.client.get(f'/employee/{PO2.id}/').json()['product'], product_3.id)
        self.assertEqual(Product.objects.get(id=product_2.id).has_owner, True)
        self.assertEqual(Product.objects.get(id=product_3.id).has_owner, True)
        self.assertEqual(self.client.post('/logout/').status_code, 200)