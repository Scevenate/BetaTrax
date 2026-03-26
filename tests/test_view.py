from django.test import TestCase
from BetaTrax.models import Employee, Product

class TestView(TestCase):
    def assertReportTitles(self, response, reports):
        n = len(reports)
        if len(response['reports']) != n:
            self.fail(f"Expected {n} reports, got {len(response['reports'])}")
        for i in range(n):
            if response['reports'][i]['title'] != reports[i]['title']:
                self.fail(f"Expected report {i} to be {reports[i]['title']}, got {response['reports'][i]['title']}")
        return True
    def assertReportTitle(self, response, report):
        if response['title'] != report['title']:
            self.fail(f"Expected report to be {report['title']}, got {response['title']}")
        return True
    def test_product_owner_view(self):
        self.product = Product.objects.create(name='Test Product')
        self.employee = Employee.objects.create_user(
            email='test@test.com',
            password='testpassword',
            role='PRODUCT_OWNER',
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
            'tester_email': 'tester@test.com',
        }]
        self.assertEqual(self.client.post('/report/', reports[0]).status_code, 201)
        self.assertEqual(self.client.post('/report/', reports[1]).status_code, 201)
        self.assertEqual(self.client.get('/report/').status_code, 403)
        self.assertEqual(self.client.post('/login/', {
            'email': self.employee.email,
            'password': 'notpassword',
        }).status_code, 403)
        self.assertEqual(self.client.post('/login/', {
            'email': self.employee.email,
            'password': 'testpassword',
        }).status_code, 200)
        self.assertReportTitles(self.client.get('/report/').json(), list(reversed(reports)))
        self.assertReportTitles(self.client.get('/report/?status=NEW').json(), list(reversed(reports)))
        self.assertReportTitles(self.client.get('/report/?status=COULDNT_REPRODUCE&page=1&sort=-priority').json(), [])
        self.assertReportTitles(self.client.get('/report/?search=Report 1').json(), [reports[0]])
        self.assertEqual(self.client.get('/report/?status=OPEN&sort=UwU').status_code, 400)
        self.assertEqual(self.client.get('/report/?status=KALTSIT&sort=-priority').status_code, 400)
        self.assertEqual(self.client.get('/report/?page=p').status_code, 400)
        self.assertEqual(self.client.get('/report/?page=2').status_code, 400)

        self.assertEqual(self.client.get('/report/14/').status_code, 404)
        self.assertReportTitle(self.client.get('/report/1/').json(), reports[0])
        self.assertReportTitle(self.client.get('/report/2/').json(), reports[1])
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.get('/report/').status_code, 403)
