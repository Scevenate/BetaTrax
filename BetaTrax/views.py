from django.core import paginator
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect, HttpResponseServerError
from .models import Employee, Product, Report, Comment, EmployeeRole, ReportStatus
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator, EmptyPage
from django.views import View

def index(request: HttpRequest):
    return HttpResponse("<h1>Server is up</h1>")

class LoginView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return HttpResponse()
        else:
            return HttpResponseForbidden()

class ReportView(View):
    def get(self, request: HttpRequest):
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")
        # Query parameters
        sort_by = request.GET.get("sort", default="-updated_at")
        if sort_by not in ("-updated_at", "-severity", "-priority"):
            return HttpResponseBadRequest("Invalid sort parameter")
        status = request.GET.get("status")
        if status not in (None, *ReportStatus.values):
            return HttpResponseBadRequest("Invalid status parameter")
        page = request.GET.get("page", default=1)
        try:
            page = int(page)
            assert page > 0
        except (ValueError, AssertionError):
            return HttpResponseBadRequest("Invalid page parameter")

        # Product owner query        
        if request.user.role == EmployeeRole.PRODUCT_OWNER:
            reports = Report.objects.filter(product=request.user.product, status=status).order_by(sort_by)
            paginator = Paginator(reports, 20)
            try:
                page_obj = paginator.page(page)
            except EmptyPage:
                return HttpResponseBadRequest("Page out of range")
            return JsonResponse({"reports": list(page_obj.object_list.values())})

        # Developer query
        elif request.user.role == EmployeeRole.DEVELOPER:
            reports = Report.objects.filter(product=request.user.product, assigned_to=request.user).order_by(sort_by)
            paginator = Paginator(reports, 20)
            try:
                page_obj = paginator.page(page)
            except EmptyPage:
                return HttpResponseBadRequest("Page out of range")
            return JsonResponse({"reports": list(page_obj.object_list.values())})
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
        except Exception as e:
            return HttpResponseBadRequest(f"Error: {e}")
        return HttpResponse("Report submitted")