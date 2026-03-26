from django.http import HttpRequest, HttpResponse, HttpResponseServerError, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from .models import Product, Report, EmployeeRole, ReportStatus, ReportAction, ReportSeverity, ReportPriority, Employee
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator, EmptyPage
from django.forms.models import model_to_dict
from django.views import View
from django.core.exceptions import ValidationError
from .email import notify_tester
import json

def index(request: HttpRequest):
    return HttpResponse("<h1>Server is up</h1>")

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
    def get(self, request: HttpRequest):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
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
            return JsonResponse({"reports": list(page_obj.object_list.values('id', 'title', 'status', 'severity', 'priority'))})

        # Developer query
        elif request.user.role == EmployeeRole.DEVELOPER:
            reports = Report.objects.filter(product=request.user.product, assigned_to=request.user)
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
            return JsonResponse({"reports": list(page_obj.object_list.values('id', 'title', 'status', 'severity', 'priority'))})
        else:
            return HttpResponseServerError("Role not supported")

    def post(self, request: HttpRequest):
        title = request.POST.get("title")
        description = request.POST.get("description")
        reproduce_steps = request.POST.get("reproduce_steps")
        product = Product.objects.get(id=request.POST.get("product"))
        tester_email = request.POST.get("tester_email") # Possibly null
        try:
            report = Report(status="NEW", title=title, description=description, reproduce_steps=reproduce_steps, product=product, tester_email=tester_email)
            report.save()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=400)
        return HttpResponse(status=201)

class ReportView(View):
    def get(self, request: HttpRequest, id: int):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        # Roles restriction
        if request.user.role == EmployeeRole.PRODUCT_OWNER:
            report = Report.objects.filter(product=request.user.product)
        elif request.user.role == EmployeeRole.DEVELOPER:
            report = Report.objects.filter(product=request.user.product, assigned_to=request.user)
        else:
            return HttpResponseServerError("Role not supported")
        # Get report
        try:
            report = report.get(id=id)
        except Report.DoesNotExist:
            return HttpResponseNotFound()
        return JsonResponse(model_to_dict(report))
    def patch(self, request: HttpRequest, id: int):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        # Get report
        report = Report.objects.filter(product=request.user.product)
        if request.user.role == EmployeeRole.PRODUCT_OWNER:
            pass
        elif request.user.role == EmployeeRole.DEVELOPER:
            report = report.filter(assigned_to=request.user)
        else:
            return HttpResponseServerError("Role not supported")
        try:
            report = report.get(id=id)
        except Report.DoesNotExist:
            return HttpResponseNotFound()
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
                severity = request.PATCH.get("severity")
                if severity is None:
                    return HttpResponseBadRequest("Severity is required")
                try:
                    severity = int(severity)
                    assert severity in ReportSeverity.values
                except (ValueError, AssertionError):
                    return HttpResponseBadRequest("Invalid severity")
                report.severity = severity
                priority = request.PATCH.get("priority")
                if priority is None:
                    return HttpResponseBadRequest("Priority is required")
                try:
                    priority = int(priority)
                    assert priority in ReportPriority.values
                except (ValueError, AssertionError):
                    return HttpResponseBadRequest("Invalid priority")
                report.priority = priority
                report.status = ReportStatus.OPENED
                report.save()
                notify_tester(report, action)
                return HttpResponse()
            case ReportAction.REJECT.value:
                if report.status != ReportStatus.NEW:
                    return HttpResponseBadRequest("Action not allowed")
                report.status = ReportStatus.REJECTED
                report.save()
                notify_tester(report, action)
                return HttpResponse()
            case ReportAction.DUPLICATE.value:
                if report.status != ReportStatus.NEW:
                    return HttpResponseBadRequest("Action not allowed")
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
                notify_tester(report, action)
                return HttpResponse()
            case ReportAction.ASSIGN.value:
                if report.status != ReportStatus.OPENED and report.status != ReportStatus.REOPENED:
                    return HttpResponseBadRequest("Action not allowed")
                assigned_to = request.PATCH.get("assigned_to")
                if assigned_to is None:
                    return HttpResponseBadRequest("assigned_to is required")
                try:
                    assigned_to = Employee.objects.get(id=assigned_to)
                except Employee.DoesNotExist:
                    return HttpResponseBadRequest("Invalid assigned_to")
                report.assigned_to = assigned_to
                report.status = ReportStatus.ASSIGNED
                report.save()
                notify_tester(report, action)
                return HttpResponse()
            case ReportAction.FIX.value:
                if report.status != ReportStatus.ASSIGNED:
                    return HttpResponseBadRequest("Action not allowed")
                report.assigned_to = None
                report.status = ReportStatus.FIXED
                report.save()
                notify_tester(report, action)
                return HttpResponse()
            case ReportAction.CANNOT_REPRODUCE.value:
                if report.status != ReportStatus.ASSIGNED:
                    return HttpResponseBadRequest("Action not allowed")
                report.assigned_to = None
                report.status = ReportStatus.COULDNT_REPRODUCE
                report.save()
                notify_tester(report, action)
                return HttpResponse()
            case ReportAction.REOPEN.value:
                if report.status != ReportStatus.FIXED:
                    return HttpResponseBadRequest("Action not allowed")
                report.assigned_to = None
                report.status = ReportStatus.REOPENED
                report.save()
                notify_tester(report, action)
                return HttpResponse()
            case ReportAction.RESOLVE.value:
                if report.status != ReportStatus.FIXED:
                    return HttpResponseBadRequest("Action not allowed")
                report.status = ReportStatus.RESOLVED
                report.save()
                notify_tester(report, action)
                return HttpResponse()
            case _:
                return HttpResponseBadRequest("Invalid action")