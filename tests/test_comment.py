from django.test import TestCase
from BetaTrax.models import Employee, Product, Report

class TestComment(TestCase):
    def assertCommentContents(self, response, comments):
        n = len(comments)
        if len(response['comments']) != n:
            self.fail(f"Expected {n} comments, got {len(response['comments'])}")
        for i in range(n):
            if response['comments'][i]['content'] != comments[i]:
                self.fail(f"Expected comment {i} to be {comments[i]}, got {response['comments'][i]['content']}")
        return True
    def test_comment(self):
        self.product = Product.objects.create(name='Test Product')
        self.employee = Employee.objects.create_user(
            email='test@test.com',
            password='testpassword',
            role='PRODUCT_OWNER',
            product=self.product.id,
        )
        self.report = Report.objects.create(
            title='Report 1',
            description='Description 1',
            reproduce_steps='Reproduce steps 1',
            product=self.product,
            tester_id='tester 1',
        )
        comments = ["Needs dev review.", 
            "No longer supported.",
            "The report seems to be addressing the side bar in android app home page.",
        ]
        self.assertEqual(self.client.post('/report/1/comments/', {
            'content': comments[0],
        }).status_code, 403)
        self.assertEqual(self.client.post('/login/', {
            'email': self.employee.email,
            'password': 'testpassword',
        }).status_code, 200)
        self.assertCommentContents(self.client.get('/report/1/comments/').json(), [])
        self.assertEqual(self.client.post('/report/1/comments/', {
            'content': comments[0],
        }).status_code, 201)
        self.assertCommentContents(self.client.get('/report/1/comments/').json(), [comments[0]])
        self.assertEqual(self.client.post('/report/1/comments/', {
            'content': comments[1],
        }).status_code, 201)
        self.assertCommentContents(self.client.get('/report/1/comments/').json(), [comments[1], comments[0]])
        self.assertEqual(self.client.post('/report/1/comments/', {
            'content': comments[2],
        }).status_code, 201)
        self.assertCommentContents(self.client.get('/report/1/comments/').json(), [comments[2], comments[1], comments[0]])