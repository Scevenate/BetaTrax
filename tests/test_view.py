from rest_framework.test import APITestCase, APIClient
from django_tenants.test.cases import TenantTestCase
from BetaTrax.models import Employee, Product, Report

class TestView(APITestCase, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient(HTTP_HOST='tenant.test.com')

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
        self.owner = Employee.objects.create_user(
            email='owner@test.com',
            password='ownerpassword',
            role='PRODUCT_OWNER',
            product=self.product.id,
        )
        self.dev = Employee.objects.create_user(
            email='dev@test.com',
            password='devpassword',
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
            'tester_email': 'tester@test.com',
        }]
        self.assertEqual(self.client.post('/report/', reports[0]).status_code, 201)
        self.assertEqual(self.client.post('/report/', reports[1]).status_code, 201)
        self.assertEqual(self.client.get('/report/').status_code, 403)
        self.assertEqual(self.client.post('/login/', {
            'email': self.owner.email,
            'password': 'notpassword',
        }).status_code, 403)
        self.assertEqual(self.client.post('/login/', {
            'email': self.owner.email,
            'password': 'ownerpassword',
        }).status_code, 200)
        self.assertReportTitles(self.client.get('/report/').json(), list(reversed(reports)))
        self.assertReportTitles(self.client.get('/report/?status=NEW').json(), list(reversed(reports)))
        self.assertReportTitles(self.client.get('/report/?status=COULDNT_REPRODUCE&page=1&sort=-priority').json(), [])
        self.assertReportTitles(self.client.get('/report/?search=Report 1').json(), [reports[0]])
        self.assertEqual(self.client.get('/report/?status=OPEN&sort=UwU').status_code, 400)
        self.assertEqual(self.client.get('/report/?status=KALTSIT&sort=-priority').status_code, 400)
        self.assertEqual(self.client.get('/report/?page=p').status_code, 400)
        self.assertEqual(self.client.get('/report/?page=2').status_code, 400)
        report_1_id = Report.objects.get(title=reports[0]['title'], product=self.product).id
        report_2_id = Report.objects.get(title=reports[1]['title'], product=self.product).id
        missing_report_id = max(report_1_id, report_2_id) + 1000
        self.assertEqual(self.client.get(f'/report/{missing_report_id}/').status_code, 404)
        self.assertReportTitle(self.client.get(f'/report/{report_1_id}/').json(), reports[0])
        self.assertReportTitle(self.client.get(f'/report/{report_2_id}/').json(), reports[1])
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.get('/report/').status_code, 403)

    def test_developer_effectiveness_metric(self):
        self.product = Product.objects.create(name='Metric Product')
        self.owner = Employee.objects.create_user(
            email='owner2@test.com',
            password='ownerpassword2',
            role='PRODUCT_OWNER',
            product=self.product.id,
        )
        self.dev = Employee.objects.create_user(
            email='dev2@test.com',
            password='devpassword2',
            role='DEVELOPER',
            product=self.product.id,
        )

        self.assertEqual(self.client.post('/login/', {
            'email': self.owner.email,
            'password': 'ownerpassword2',
        }).status_code, 200)

        # Create and open reports, assign and fix many of them by the developer.
        report_ids = []
        for i in range(33):
            response = self.client.post('/report/', {
                'title': f'Report {i+1}',
                'description': f'Description {i+1}',
                'reproduce_steps': f'Steps {i+1}',
                'product': self.product.id,
                'tester_id': f'tester {i+1}',
            })
            self.assertEqual(response.status_code, 201)
            report_ids.append(Report.objects.get(title=f'Report {i+1}', product=self.product).id)

            # Open the report as product owner.
            self.assertEqual(self.client.patch(f'/report/{report_ids[-1]}/', {
                'action': 'OPEN',
                'severity': 'LOW',
                'priority': 'LOW',
            }).status_code, 200)

        # Log in as developer to assign and fix reports.
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': self.dev.email,
            'password': 'devpassword2',
        }).status_code, 200)

        for report_id in report_ids:
            self.assertEqual(self.client.patch(f'/report/{report_id}/', {'action': 'ASSIGN'}).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_id}/', {'action': 'FIX'}).status_code, 200)

        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': self.owner.email,
            'password': 'ownerpassword2',
        }).status_code, 200)

        # Reopen one report to create a reopen count.
        self.assertEqual(self.client.patch(f'/report/{report_ids[0]}/', {'action': 'REOPEN'}).status_code, 200)

        # Request developer effectiveness.
        response = self.client.get(f'/employee/{self.dev.id}/effectiveness/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['fixed_count'], 33)
        self.assertEqual(data['reopened_count'], 1)
        self.assertEqual(data['effectiveness'], 'Good')