from django.http import HttpRequest, HttpResponse, HttpResponseServerError, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from .models import Product, Report, EmployeeRole, ReportStatus, ReportAction, ReportSeverity, ReportPriority, Employee, Comment
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator, EmptyPage
from django.forms.models import model_to_dict
from django.views import View
from django.core.exceptions import ValidationError
from .email import notify_tester_status
import json
from functools import wraps
from django.shortcuts import get_object_or_404

def index(request: HttpRequest):
    return HttpResponse("<h1>Server is up</h1>")

def logged_in_check(func):
    @wraps(func)
    def wrapper(self, request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        return func(self, request, *args, **kwargs)
    return wrapper

class LoginView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return HttpResponseForbidden()
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return HttpResponse()
        else:
            return HttpResponseForbidden()

class LogoutView(View):
    def post(self, request: HttpRequest):
        logout(request)
        return HttpResponse()

class ReportsView(View):
    @logged_in_check
    def get(self, request: HttpRequest):
        # Query parameters
        search = request.GET.get("search") # None is all
        sort_by = request.GET.get("sort", default="-updated_at")
        if sort_by not in ("-updated_at", "-severity", "-priority"):
            return HttpResponseBadRequest("Invalid sort parameter")
        status = request.GET.get("status")
        if status not in (None, *ReportStatus.values): # None is ALL
            return HttpResponseBadRequest("Invalid status parameter")
        page = request.GET.get("page", default=1)
        try:
            page = int(page)
            assert page > 0
        except (ValueError, AssertionError):
            return HttpResponseBadRequest("Invalid page parameter")

        # Product owner query        
        if request.user.role == EmployeeRole.PRODUCT_OWNER:
            reports = Report.objects.filter(product=request.user.product)
            if search:
                reports = reports.filter(title__icontains=search)
            if status:
                reports = reports.filter(status=status)
            reports = reports.order_by(sort_by)
            paginator = Paginator(reports, 20)
            try:
                page_obj = paginator.page(page)
            except EmptyPage:
                return HttpResponseBadRequest("Page out of range")
            
            reports = list(page_obj.object_list.values('id', 'title', 'status', 'severity', 'priority'))
            # Map integer back to string value
            for report in reports:
                if report['severity'] is not None:
                    report['severity'] = ReportSeverity(report['severity']).label
                
                if report['priority'] is not None:
                    report['priority'] = ReportPriority(report['priority']).label
            
            return JsonResponse({"reports": reports})

        # Developer query
        elif request.user.role == EmployeeRole.DEVELOPER:
            # reports = Report.objects.filter(Q(assigned_to=request.user) | Q(status=ReportStatus.OPENED) | Q(status=ReportStatus.REOPENED), product=request.user.product)
            reports = Report.objects.filter(product=request.user.product)
            if search:
                reports = reports.filter(title__icontains=search)
            if status:
                reports = reports.filter(status=status)
            reports = reports.order_by(sort_by)
            paginator = Paginator(reports, 20)
            try:
                page_obj = paginator.page(page)
            except EmptyPage:
                return HttpResponseBadRequest("Page out of range")
            
            reports = list(page_obj.object_list.values('id', 'title', 'status', 'severity', 'priority'))
            # Map integer back to string value
            for report in reports:
                if report['severity'] is not None:
                    report['severity'] = ReportSeverity(report['severity']).label
                
                if report['priority'] is not None:
                    report['priority'] = ReportPriority(report['priority']).label
            
            return JsonResponse({"reports": reports})
        else:
            return HttpResponseServerError("Role not supported")

    def post(self, request: HttpRequest):
        title = request.POST.get("title")
        description = request.POST.get("description")
        reproduce_steps = request.POST.get("reproduce_steps")
        product = Product.objects.get(id=request.POST.get("product"))
        version = request.POST.get("version")
        tester_id = request.POST.get("tester_id")
        tester_email = request.POST.get("tester_email") # Possibly null
        try:
            report = Report(status="NEW", title=title, description=description, reproduce_steps=reproduce_steps, product=product, version=version, tester_id=tester_id, tester_email=tester_email)
            report.save()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=400)
        return HttpResponse(status=201)

class ReportView(View):
    @logged_in_check
    def get(self, request: HttpRequest, id: int):
        report = get_object_or_404(Report, id=id, product=request.user.product)
        report = model_to_dict(report)
        # map int to string
        if report['severity'] is not None:
            report['severity'] = ReportSeverity(report['severity']).label
        
        if report['priority'] is not None:
            report['priority'] = ReportPriority(report['priority']).label
        return JsonResponse(report)

    @logged_in_check
    def patch(self, request: HttpRequest, id: int):
        # Get report
        severity_map = {
            "CRITICAL" : 3,
            "MAJOR" : 2,
            "MINOR" : 1,
            "LOW" : 0
        }

        priority_map = {
            "CRITICAL" : 3,
            "HIGH" : 2,
            "MEDIUM" : 1,
            "LOW" : 0
        }
        report = get_object_or_404(Report, id=id, product=request.user.product)
        # Action validation
        request.PATCH = json.loads(request.body)
        action = request.PATCH.get("action")
        if action is None:
            return HttpResponseBadRequest("Action is required")
        # Action execution
        match action:
            case ReportAction.OPEN.value:
                if report.status != ReportStatus.NEW:
                    return HttpResponseBadRequest("Action not allowed")
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return HttpResponseForbidden()
                severity = request.PATCH.get("severity")
                if severity is None:
                    return HttpResponseBadRequest("Severity is required")
                try:
                    severity = severity_map.get(severity)
                    assert severity in ReportSeverity.values
                except (ValueError, AssertionError):
                    return HttpResponseBadRequest("Invalid severity")
                report.severity = severity
                priority = request.PATCH.get("priority")
                if priority is None:
                    return HttpResponseBadRequest("Priority is required")
                try:
                    priority = priority_map.get(priority)
                    assert priority in ReportPriority.values
                except (ValueError, AssertionError):
                    return HttpResponseBadRequest("Invalid priority")
                report.priority = priority
                report.status = ReportStatus.OPENED
                report.save()
                notify_tester_status(report, report.status.value)
                return HttpResponse()
            case ReportAction.REJECT.value:
                if report.status != ReportStatus.NEW:
                        return HttpResponseBadRequest("Action not allowed")
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return HttpResponseForbidden()
                report.status = ReportStatus.REJECTED
                report.save()
                notify_tester_status(report, report.status.value)
                return HttpResponse()
            case ReportAction.DUPLICATE.value:
                if report.status != ReportStatus.NEW:
                    return HttpResponseBadRequest("Action not allowed")
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return HttpResponseForbidden()
                duplicate_of = request.PATCH.get("duplicate_of")
                if duplicate_of is None:
                    return HttpResponseBadRequest("duplicate_of must be specified")
                try:
                    duplicate_of = Report.objects.get(id=duplicate_of)
                except Report.DoesNotExist:
                    return HttpResponseBadRequest("Invalid duplicate of")
                report.duplicate_of = duplicate_of
                report.status = ReportStatus.DUPLICATED
                report.save()
                notify_tester_status(report, report.status.value)
                return HttpResponse()
            case ReportAction.ASSIGN.value:
                if report.status != ReportStatus.OPENED and report.status != ReportStatus.REOPENED:
                    return HttpResponseBadRequest("Action not allowed")
                if request.user.role != EmployeeRole.DEVELOPER:
                    return HttpResponseForbidden()
                report.assigned_to = request.user
                report.status = ReportStatus.ASSIGNED
                report.save()
                notify_tester_status(report, report.status.value)
                return HttpResponse()
            case ReportAction.FIX.value:
                if report.status != ReportStatus.ASSIGNED:
                    return HttpResponseBadRequest("Action not allowed")
                if request.user.role != EmployeeRole.DEVELOPER:
                    return HttpResponseForbidden()
                report.assigned_to = None
                report.status = ReportStatus.FIXED
                report.save()
                notify_tester_status(report, report.status.value)
                return HttpResponse()
            case ReportAction.CANNOT_REPRODUCE.value:
                if report.status != ReportStatus.ASSIGNED:
                    return HttpResponseBadRequest("Action not allowed")
                if request.user.role != EmployeeRole.DEVELOPER:
                    return HttpResponseForbidden()
                report.assigned_to = None
                report.status = ReportStatus.COULDNT_REPRODUCE
                report.save()
                notify_tester_status(report, report.status.value)
                return HttpResponse()
            case ReportAction.REOPEN.value:
                if report.status != ReportStatus.FIXED:
                    return HttpResponseBadRequest("Action not allowed")
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return HttpResponseForbidden()
                report.assigned_to = None
                report.status = ReportStatus.REOPENED
                report.save()
                notify_tester_status(report, report.status.value)
                return HttpResponse()
            case ReportAction.RESOLVE.value:
                if report.status != ReportStatus.FIXED:
                    return HttpResponseBadRequest("Action not allowed")
                if request.user.role != EmployeeRole.PRODUCT_OWNER:
                    return HttpResponseForbidden()
                report.status = ReportStatus.RESOLVED
                report.save()
                notify_tester_status(report, report.status.value)
                return HttpResponse()
            case _:
                return HttpResponseBadRequest("Invalid action")

class CommentsView(View):
    @logged_in_check
    def get(self, request: HttpRequest, id: int):
        # Get report
        report = get_object_or_404(Report, id=id, product=request.user.product)
        # Get comments
        return JsonResponse({"comments": list(Comment.objects.filter(report=report).order_by('-created_at').values('id', 'employee', 'content'))})
    
    @logged_in_check
    def post(self, request: HttpRequest, id: int):
        # Get report
        report = get_object_or_404(Report, id=id, product=request.user.product)
        # Create comment
        content = request.POST.get("content")
        if content is None:
            return HttpResponseBadRequest("content is required")
        comment = Comment(report=report, employee=request.user, content=content)
        comment.save()
        return HttpResponse(status=201)