from .models import *
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator, EmptyPage
from django.forms.models import model_to_dict
from django.core.exceptions import ValidationError
from django.db import transaction
from .email import notify_all_testers_status
from functools import wraps
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def index(request: Request) -> Response:
    return Response(status=status.HTTP_200_OK, data={"message": "Server is up"})

def logged_in_check(func):
    @wraps(func)
    def wrapper(self, request: Request, *args, **kwargs) -> Response:
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authenticated"})
        return func(self, request, *args, **kwargs)
    return wrapper

class LoginView(APIView):
    def post(self, request: Request) -> Response:
        if request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User is already authenticated"})
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "Invalid credentials"})

class LogoutView(APIView):
    def post(self, request: Request) -> Response:
        logout(request)
        return Response(status=status.HTTP_200_OK)

class ReportsView(APIView):
    @logged_in_check
    def get(self, request: Request) -> Response:
        # Query parameters
        query_search = request.query_params.get("search") # None is all
        query_sort_by = request.query_params.get("sort", "-updated_at")
        if query_sort_by not in ("-updated_at", "-severity", "-priority"):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Invalid sort parameter"})
        query_status = request.query_params.get("status")
        if query_status not in (None, *ReportStatus.values): # None is ALL
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Invalid status parameter"})
        page = request.query_params.get("page", 1)
        try:
            page = int(page)
            assert page > 0
        except (ValueError, AssertionError):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Invalid page parameter"})

        # Product owner query        
        if request.user.role == EmployeeRole.PRODUCT_OWNER:
            reports = Report.objects.filter(product=request.user.product)
            if query_search:
                reports = reports.filter(title__icontains=query_search)
            if query_status:
                reports = reports.filter(status=query_status)
            reports = reports.order_by(query_sort_by)
            paginator = Paginator(reports, 20)
            try:
                page_obj = paginator.page(page)
            except EmptyPage:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Page out of range"})
            
            reports = list(page_obj.object_list.values('id', 'title', 'status', 'severity', 'priority'))
            # Map integer back to string value
            for report in reports:
                if report['severity'] is not None:
                    report['severity'] = ReportSeverity(report['severity']).label
                
                if report['priority'] is not None:
                    report['priority'] = ReportPriority(report['priority']).label
            
            return Response(status=status.HTTP_200_OK, data={"reports": reports})

        # Developer query
        elif request.user.role == EmployeeRole.DEVELOPER:
            # reports = Report.objects.filter(Q(assigned_to=request.user) | Q(status=ReportStatus.OPENED) | Q(status=ReportStatus.REOPENED), product=request.user.product)
            reports = Report.objects.filter(product=request.user.product)
            if query_search:
                reports = reports.filter(title__icontains=query_search)
            if query_status:
                reports = reports.filter(status=query_status)
            reports = reports.order_by(query_sort_by)
            paginator = Paginator(reports, 20)
            try:
                page_obj = paginator.page(page)
            except EmptyPage:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Page out of range"})
            
            reports = list(page_obj.object_list.values('id', 'title', 'status', 'severity', 'priority'))
            # Map integer back to string value
            for report in reports:
                if report['severity'] is not None:
                    report['severity'] = ReportSeverity(report['severity']).label
                
                if report['priority'] is not None:
                    report['priority'] = ReportPriority(report['priority']).label
            
            return Response(status=status.HTTP_200_OK, data={"reports": reports})
        else:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})

    def post(self, request: Request) -> Response:
        title = request.data.get("title")
        description = request.data.get("description")
        reproduce_steps = request.data.get("reproduce_steps")
        product = Product.objects.get(id=request.data.get("product"))
        version = request.data.get("version")
        tester_id = request.data.get("tester_id")
        tester_email = request.data.get("tester_email") # Possibly null
        try:
            report = Report(status="NEW", title=title, description=description, reproduce_steps=reproduce_steps, product=product, version=version, tester_id=tester_id, tester_email=tester_email)
            report.save()
        except ValidationError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": str(e.message_dict)})
        return Response(status=status.HTTP_201_CREATED)

class ReportView(APIView):
    @logged_in_check
    def get(self, request: Request, id: int) -> Response:
        report = get_object_or_404(Report, id=id, product=request.user.product)
        report = model_to_dict(report)
        # map int to string
        if report['severity'] is not None:
            report['severity'] = ReportSeverity(report['severity']).label
        
        if report['priority'] is not None:
            report['priority'] = ReportPriority(report['priority']).label
        return Response(status=status.HTTP_200_OK, data=report)

    @logged_in_check
    def patch(self, request: Request, id: int) -> Response:
        # Get report
        report = get_object_or_404(Report, id=id, product=request.user.product)
        action = request.data.get("action")
        if action is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Action is required"})
        # Action execution
        match action:
            case ReportAction.OPEN.value:
                if report.status != ReportStatus.NEW:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Action not allowed"})
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
                severity = request.data.get("severity")
                if severity is None:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Severity is required"})
                try:
                    severity = ReportSeverity[severity]
                except KeyError:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Invalid severity"})
                report.severity = severity
                priority = request.data.get("priority")
                if priority is None:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Priority is required"})
                try:
                    priority = ReportPriority[priority]
                except KeyError:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Invalid priority"})
                report.priority = priority
                report.status = ReportStatus.OPENED
                report.save()
                notify_all_testers_status(report, report.status.value)
                return Response(status=status.HTTP_200_OK)
            case ReportAction.REJECT.value:
                if report.status != ReportStatus.NEW:
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Action not allowed"})
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
                report.status = ReportStatus.REJECTED
                report.save()
                notify_all_testers_status(report, report.status.value)
                return Response(status=status.HTTP_200_OK)
            case ReportAction.DUPLICATE.value:
                if report.status != ReportStatus.NEW:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Action not allowed"})
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
                duplicate_of = request.data.get("duplicate_of")
                if duplicate_of is None:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "duplicate_of must be specified"})
                try:
                    duplicate_of = Report.objects.get(id=duplicate_of)
                except Report.DoesNotExist:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Invalid duplicate of"})
                report.duplicate_of = duplicate_of
                report.status = ReportStatus.DUPLICATED
                report.save()
                notify_all_testers_status(report, report.status.value)
                return Response(status=status.HTTP_200_OK)
            case ReportAction.ASSIGN.value:
                if report.status != ReportStatus.OPENED and report.status != ReportStatus.REOPENED:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Action not allowed"})
                if request.user.role != EmployeeRole.DEVELOPER:
                    return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
                report.assigned_to = request.user
                report.status = ReportStatus.ASSIGNED
                report.save()
                notify_all_testers_status(report, report.status.value)
                return Response(status=status.HTTP_200_OK)
            case ReportAction.FIX.value:
                if report.status != ReportStatus.ASSIGNED:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Action not allowed"})
                if request.user.role != EmployeeRole.DEVELOPER:
                    return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
                report.assigned_to = None
                report.status = ReportStatus.FIXED
                report.save()
                FixRecord(report=report, developer=request.user).save()
                notify_all_testers_status(report, report.status.value)
                return Response(status=status.HTTP_200_OK)
            case ReportAction.CANNOT_REPRODUCE.value:
                if report.status != ReportStatus.ASSIGNED:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Action not allowed"})
                if request.user.role != EmployeeRole.DEVELOPER:
                    return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
                report.assigned_to = None
                report.status = ReportStatus.COULDNT_REPRODUCE
                report.save()
                notify_all_testers_status(report, report.status.value)
                return Response(status=status.HTTP_200_OK)
            case ReportAction.REOPEN.value:
                if report.status != ReportStatus.FIXED:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Action not allowed"})
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
                last_fix = FixRecord.objects.filter(report=report).order_by('-created_at').first()
                fixed_by = last_fix.developer if last_fix is not None else None
                report.assigned_to = None
                report.status = ReportStatus.REOPENED
                report.save()
                ReopenRecord(report=report, fixed_by=fixed_by).save()
                notify_all_testers_status(report, report.status.value)
                return Response(status=status.HTTP_200_OK)
            case ReportAction.RESOLVE.value:
                if report.status != ReportStatus.FIXED:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Action not allowed"})
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
                report.assigned_to = None
                report.status = ReportStatus.RESOLVED
                report.save()
                notify_all_testers_status(report, report.status.value)
                return Response(status=status.HTTP_200_OK)
            case _:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Invalid action"})

class DeveloperEffectivenessView(APIView):
    @logged_in_check
    def get(self, request: Request, id: int) -> Response:
        developer = get_object_or_404(Employee, id=id, role=EmployeeRole.DEVELOPER)
        if request.user.is_superuser:
            pass
        elif request.user.role == EmployeeRole.DEVELOPER:
            if request.user.id != developer.id:
                return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
        elif request.user.role == EmployeeRole.PRODUCT_OWNER:
            if developer.product != request.user.product:
                return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
        else:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})

        fixed_count = FixRecord.objects.filter(developer=developer).count()
        reopened_count = ReopenRecord.objects.filter(fixed_by=developer).count()
        ratio = None
        if fixed_count:
            ratio = reopened_count / fixed_count

        if fixed_count < 20:
            effectiveness = "Insufficient data"
        elif ratio < 1/32:
            effectiveness = "Good"
        elif ratio < 1/8:
            effectiveness = "Fair"
        else:
            effectiveness = "Poor"

        return Response(status=status.HTTP_200_OK, data={
            "developer_id": developer.id,
            "email": developer.email,
            "fixed_count": fixed_count,
            "reopened_count": reopened_count,
            "ratio": ratio,
            "effectiveness": effectiveness,
        })

class CommentsView(APIView):
    @logged_in_check
    def get(self, request: Request, id: int) -> Response:
        # Get report
        report = get_object_or_404(Report, id=id, product=request.user.product)
        # Get comments
        return Response(status=status.HTTP_200_OK, data={"comments": list(Comment.objects.filter(report=report).order_by('-created_at').values('id', 'employee', 'content'))})
    
    @logged_in_check
    def post(self, request: Request, id: int) -> Response:
        # Get report
        report = get_object_or_404(Report, id=id, product=request.user.product)
        # Create comment
        content = request.data.get("content")
        if content is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "content is required"})
        comment = Comment(report=report, employee=request.user, content=content)
        comment.save()
        return Response(status=status.HTTP_201_CREATED)

class ProductsView(APIView):
    @logged_in_check
    def get(self, request: Request) -> Response:
        # Pagination
        page = request.query_params.get("page", 1)
        try:
            page = int(page)
            assert page > 0
        except (ValueError, AssertionError):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Invalid page parameter"})
    
        products = Product.objects.all()
        paginator = Paginator(products, 20)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Page out of range"})
        
        products = list(page_obj.object_list.values('id', 'name', 'has_owner'))
        return Response(status=status.HTTP_200_OK, data={"products": products})

    @logged_in_check
    def post(self, request: Request) -> Response:
        if request.user.role != EmployeeRole.PRODUCT_OWNER:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
        name = request.data.get("name")
        if name is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Name is required"})
        product = Product(name=name)
        try:
            product.save()
        except ValidationError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": str(e.message_dict)})
        return Response(status=status.HTTP_201_CREATED)

class EmployeeView(APIView):
    @logged_in_check
    def get(self, request: Request, id: int) -> Response:
        employee = get_object_or_404(Employee.objects.all().values('id', 'email', 'role', 'product'), id=id)
        return Response(status=status.HTTP_200_OK, data=employee)
    
    @logged_in_check
    def patch(self, request: Request, id: int) -> Response:
        # ID validation
        if request.user.id != id:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "User not authorized"})
        employee = Employee.objects.get(id=id)
        # Product assignment
        product_id = request.data.get("product")
        if product_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "product is required"})
        product = get_object_or_404(Product, id=product_id)
        # if already is the same
        if employee.product_id == product.id:
            return Response(status=status.HTTP_200_OK)
        
        if request.user.role == EmployeeRole.PRODUCT_OWNER:
            if product.has_owner:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Product already has owner"})
            # if error during process, return previous state, will not have partial update
            with transaction.atomic():
                current_product = employee.product
                # release previous product if have
                if current_product is not None:
                    current_product.has_owner = False
                    current_product.save()

                employee.product = product
                employee.save()

                product.has_owner = True
                product.save()
        elif request.user.role == EmployeeRole.DEVELOPER:
            employee.product = product
            employee.save()
        return Response(status=status.HTTP_200_OK)
