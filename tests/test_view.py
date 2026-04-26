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
        """Test all branches of DeveloperEffectivenessView authorization."""
        # === Branch 1: Superuser can access any developer's effectiveness ===
        self.product = Product.objects.create(name='Superuser Test Product')
        self.dev = Employee.objects.create_user(
            email='dev_super@test.com',
            password='devpassword',
            role='DEVELOPER',
            product=self.product.id,
        )
        self.superuser = Employee.objects.create_superuser(
            email='superuser@test.com',
            password='superpassword',
        )
        self.assertEqual(self.client.post('/login/', {
            'email': self.superuser.email,
            'password': 'superpassword',
        }).status_code, 200)
        response = self.client.get(f'/employee/{self.dev.id}/effectiveness/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post('/logout/').status_code, 200)

        # === Branch 2: Developer can access their own effectiveness ===
        self.dev_own = Employee.objects.create_user(
            email='dev_own@test.com',
            password='devpassword',
            role='DEVELOPER',
            product=self.product.id,
        )
        self.assertEqual(self.client.post('/login/', {
            'email': self.dev_own.email,
            'password': 'devpassword',
        }).status_code, 200)
        response = self.client.get(f'/employee/{self.dev_own.id}/effectiveness/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post('/logout/').status_code, 200)

        # === Branch 3: Developer cannot access another developer's effectiveness ===
        self.dev_other = Employee.objects.create_user(
            email='dev_other@test.com',
            password='devpassword',
            role='DEVELOPER',
            product=self.product.id,
        )
        self.assertEqual(self.client.post('/login/', {
            'email': self.dev_own.email,
            'password': 'devpassword',
        }).status_code, 200)
        response = self.client.get(f'/employee/{self.dev_other.id}/effectiveness/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post('/logout/').status_code, 200)

        # === Branch 4: Product owner can access developer's from same product ===
        self.product2 = Product.objects.create(name='Same Product')
        self.owner = Employee.objects.create_user(
            email='owner_same@test.com',
            password='ownerpassword',
            role='PRODUCT_OWNER',
            product=self.product2.id,
        )
        self.dev_same = Employee.objects.create_user(
            email='dev_same@test.com',
            password='devpassword',
            role='DEVELOPER',
            product=self.product2.id,
        )
        self.assertEqual(self.client.post('/login/', {
            'email': self.owner.email,
            'password': 'ownerpassword',
        }).status_code, 200)
        response = self.client.get(f'/employee/{self.dev_same.id}/effectiveness/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post('/logout/').status_code, 200)

        # === Branch 5: Product owner cannot access developer's from different product ===
        self.product3 = Product.objects.create(name='Different Product')
        self.owner_diff = Employee.objects.create_user(
            email='owner_diff@test.com',
            password='ownerpassword',
            role='PRODUCT_OWNER',
            product=self.product3.id,
        )
        self.dev_diff = Employee.objects.create_user(
            email='dev_diff@test.com',
            password='devpassword',
            role='DEVELOPER',
            product=self.product.id,  # different product
        )
        self.assertEqual(self.client.post('/login/', {
            'email': self.owner_diff.email,
            'password': 'ownerpassword',
        }).status_code, 200)
        response = self.client.get(f'/employee/{self.dev_diff.id}/effectiveness/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post('/logout/').status_code, 200)

        # === Branch 6: User with no role (invalid role) cannot access developer effectiveness ===
        self.user_no_role = Employee.objects.create_user(
            email='norole@test.com',
            password='norolepassword',
            role='',  # empty role is invalid
            product=self.product2.id,
        )
        self.assertEqual(self.client.post('/login/', {
            'email': self.user_no_role.email,
            'password': 'norolepassword',
        }).status_code, 200)
        response = self.client.get(f'/employee/{self.dev_same.id}/effectiveness/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        
        # ============================================================
        # COUNTING PART: Test all 4 effectiveness classifications
        # ============================================================

        self.product_count = Product.objects.create(name='Count Product')
        self.owner_count = Employee.objects.create_user(
            email='owner_count@test.com',
            password='ownerpassword',
            role='PRODUCT_OWNER',
            product=self.product_count.id,
        )
        self.dev_count = Employee.objects.create_user(
            email='dev_count@test.com',
            password='devpassword',
            role='DEVELOPER',
            product=self.product_count.id,
        )

        self.assertEqual(self.client.post('/login/', {
            'email': self.owner_count.email,
            'password': 'ownerpassword',
        }).status_code, 200)

        # --- Branch 7: "Insufficient data" + ratio=None (0 fixes) ---
        response = self.client.get(f'/employee/{self.dev_count.id}/effectiveness/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['fixed_count'], 0)
        self.assertIsNone(response.json()['ratio'])
        self.assertEqual(response.json()['effectiveness'], 'Insufficient data')

        # Create 33 reports and open them
        report_ids = []
        for i in range(33):
            response = self.client.post('/report/', {
                'title': f'Report {i+1}',
                'description': f'Description {i+1}',
                'reproduce_steps': f'Steps {i+1}',
                'product': self.product_count.id,
                'tester_id': f'tester {i+1}',
            })
            self.assertEqual(response.status_code, 201)
            report_ids.append(Report.objects.get(title=f'Report {i+1}', product=self.product_count).id)
            self.assertEqual(self.client.patch(f'/report/{report_ids[-1]}/', {
                'action': 'OPEN',
                'severity': 'LOW',
                'priority': 'LOW',
            }).status_code, 200)

        # Log in as developer and fix all 33
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': self.dev_count.email,
            'password': 'devpassword',
        }).status_code, 200)
        for report_id in report_ids:
            self.assertEqual(self.client.patch(f'/report/{report_id}/', {'action': 'ASSIGN'}).status_code, 200)
            self.assertEqual(self.client.patch(f'/report/{report_id}/', {'action': 'FIX'}).status_code, 200)

        # Back to owner to view results
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': self.owner_count.email,
            'password': 'ownerpassword',
        }).status_code, 200)

        # --- Branch 8: "Good" (33 fixes, 0 reopens, ratio=0.0 < 1/32) ---
        response = self.client.get(f'/employee/{self.dev_count.id}/effectiveness/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['fixed_count'], 33)
        self.assertEqual(response.json()['reopened_count'], 0)
        self.assertEqual(response.json()['effectiveness'], 'Good')

        # --- Branch 9: "Fair" (reopen 3 reports: ratio=3/33=0.09, between 1/32 and 1/8) ---
        self.assertEqual(self.client.post('/logout/').status_code, 200)
        self.assertEqual(self.client.post('/login/', {
            'email': self.owner_count.email,
            'password': 'ownerpassword',
        }).status_code, 200)
        for i in range(3):
            self.assertEqual(self.client.patch(f'/report/{report_ids[i]}/', {'action': 'REOPEN'}).status_code, 200)
        response = self.client.get(f'/employee/{self.dev_count.id}/effectiveness/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reopened_count'], 3)
        self.assertEqual(response.json()['effectiveness'], 'Fair')

        # --- Branch 10: "Poor" (reopen 2 more: ratio=5/33=0.15 > 1/8) ---
        for i in range(3, 5):
            self.assertEqual(self.client.patch(f'/report/{report_ids[i]}/', {'action': 'REOPEN'}).status_code, 200)
        response = self.client.get(f'/employee/{self.dev_count.id}/effectiveness/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reopened_count'], 5)
        self.assertEqual(response.json()['effectiveness'], 'Poor')