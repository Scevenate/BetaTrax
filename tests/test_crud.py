from rest_framework.test import APITestCase, APIClient
from BetaTrax.models import Product, Employee, Report
from unittest.mock import patch
from django_tenants.test.cases import TenantTestCase

class TestCrud(APITestCase, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient(HTTP_HOST='tenant.test.com')

    def assert_email_output(self, mock_send):
        expected_output = [
            "[Email] TO: tester1@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 1 has been updated to OPENED.",
            "[Email] TO: tester3@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 3 has been updated to OPENED.",
            "[Email] TO: tester1@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 1 has been updated to ASSIGNED.",
            "[Email] TO: tester3@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 3 has been updated to ASSIGNED.",
            "[Email] TO: tester1@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 1 has been updated to FIXED.",
            "[Email] TO: tester3@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 3 has been updated to FIXED.",
            "[Email] TO: tester2@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 2 has been updated to DUPLICATED.",
            "[Email] TO: tester1@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 1 has been updated to REOPENED.",
            "[Email] TO: tester2@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 2 has been updated to REOPENED.",
            "[Email] TO: tester3@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 3 has been updated to RESOLVED.",
            "[Email] TO: tester1@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 1 has been updated to ASSIGNED.",
            "[Email] TO: tester2@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 2 has been updated to ASSIGNED.",
            "[Email] TO: tester1@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 1 has been updated to FIXED.",
            "[Email] TO: tester2@test.com, SUBJECT: Report Updated, MESSAGE: Your report Report 2 has been updated to FIXED.",
        ]
        actual_output = [
            f"[Email] TO: {args[0]}, SUBJECT: {args[1]}, MESSAGE: {args[2]}"
            for args, _ in mock_send.call_args_list
        ]
        self.assertEqual(actual_output, expected_output)

    def test_actions(self):
        with patch('BetaTrax.email.send') as mock_send:
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
                'tester_email': 'tester1@test.com',
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
            report_1_id = Report.objects.get(title=reports[0]['title'], product=self.product).id
            report_2_id = Report.objects.get(title=reports[1]['title'], product=self.product).id
            report_3_id = Report.objects.get(title=reports[2]['title'], product=self.product).id
            self.assertEqual(self.client.post('/login/', {
                'email': self.owner.email,
                'password': 'ownerpassword',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_1_id}/', {
                'action': 'OPEN',
                'severity': 'MAJOR',
                'priority': 'HIGH',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_3_id}/', {
                'action': 'OPEN',
                'severity': 'CRITICAL',
                'priority': 'LOW',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_1_id}/', {
                'action': 'ASSIGN',
            }).status_code, 403)
            self.assertEqual(self.client.post('/login/', {
                'email': self.developer.email,
                'password': 'developerpassword',
            }).status_code, 403)
            self.assertEqual(self.client.post('/logout/').status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_2_id}/', {
                'action': 'DUPLICATE',
                'duplicate_of': report_1_id,
            }).status_code, 403)
            self.assertEqual(self.client.post('/login/', {
                'email': self.developer.email,
                'password': 'developerpassword',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_1_id}/', {
                'action': 'ASSIGN',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_3_id}/', {
                'action': 'ASSIGN',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_2_id}/', {
                'action': 'DUPLICATE',
                'duplicate_of': report_1_id,
            }).status_code, 403)
            self.assertEqual(self.client.patch(f'/report/{report_1_id}/', {
                'action': 'FIX',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_3_id}/', {
                'action': 'FIX',
            }).status_code, 200)
            self.assertEqual(self.client.post('/logout/').status_code, 200)
            self.assertEqual(self.client.post('/login/', {
                'email': self.owner.email,
                'password': 'ownerpassword',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_2_id}/', {
                'action': 'DUPLICATE',
                'duplicate_of': report_1_id,
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_1_id}/', {
                'action': 'REOPEN',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_3_id}/', {
                'action': 'RESOLVE',
            }).status_code, 200)
            self.assertEqual(self.client.post('/logout/').status_code, 200)
            self.assertEqual(self.client.post('/login/', {
                'email': self.developer.email,
                'password': 'developerpassword',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_1_id}/', {
                'action': 'FIX',
            }).status_code, 400)
            self.assertEqual(self.client.patch(f'/report/{report_1_id}/', {
                'action': 'RESOLVE',
            }).status_code, 400)
            self.assertEqual(self.client.patch(f'/report/{report_1_id}/', {
                'action': 'ASSIGN',
            }).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_1_id}/', {
                'action': 'FIX',
            }).status_code, 200)
            self.assertEqual(self.client.post('/logout/').status_code, 200)

            self.assert_email_output(mock_send)