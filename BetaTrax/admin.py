from django.contrib import admin
from .models import Employee, Product, Report, Comment

# Register your models here.
admin.site.register(Employee)
admin.site.register(Product)
admin.site.register(Report)
admin.site.register(Comment)