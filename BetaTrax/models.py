from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from enum import Enum

class EmployeeManager(BaseUserManager):
    def create_user(self, email, password, product,**extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        product = Product.objects.get(id=product)
        user = self.model(email=email, product=product, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, product, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        return self.create_user(email, password, product, **extra_fields)

class EmployeeRole(models.TextChoices):
    PRODUCT_OWNER = "PRODUCT_OWNER"
    DEVELOPER = "DEVELOPER"

class Employee(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=EmployeeRole)
    product = models.ForeignKey("Product", on_delete=models.RESTRICT)
    objects = EmployeeManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role', 'product']

    def __str__(self):
        return self.email

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class ReportStatus(models.TextChoices):
    NEW = "NEW"
    # NEW TO:
    OPENED = "OPENED"
    REJECTED = "REJECTED" #DEAD STATE
    DUPLICATED = "DUPLICATED" # DEAD STATE
    # OPENED / REOPENED TO:
    ASSIGNED = "ASSIGNED"
    # ASSIGNED TO:
    FIXED = "FIXED"
    COULDNT_REPRODUCE = "COULDNT_REPRODUCE" # DEAD STATE
    # FIXED TO:
    REOPENED = "REOPENED" # MAY BE REASSIGNED
    RESOLVED = "RESOLVED" # DEAD STATE

class ReportAction(Enum):
    # ASSIGN, FIX and CANNOT_REPRODUCE are dev actions. Rest are product owner actions.
    # FROM NEW:
    OPEN = "OPEN" # TO OPENED
    REJECT = "REJECT" # TO REJECTED
    DUPLICATE = "DUPLICATE" # TO DUPLICATED
    # FROM OPENED / REOPENED:
    ASSIGN = "ASSIGN" # TO ASSIGNED
    # FROM ASSIGNED:
    FIX = "FIX" # TO FIXED
    CANNOT_REPRODUCE = "CANNOT_REPRODUCE" # TO COULDNT_REPRODUCE
    # FROM FIXED:
    REOPEN = "REOPEN" # TO REOPENED
    RESOLVE = "RESOLVE" # TO RESOLVED

class ReportSeverity(models.IntegerChoices):
    CRITICAL = 3
    MAJOR = 2
    MINOR = 1
    LOW = 0

class ReportPriority(models.IntegerChoices):
    CRITICAL = 3
    HIGH = 2
    MEDIUM = 1
    LOW = 0

class Report(models.Model):
    id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=20, choices=ReportStatus)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    severity = models.IntegerField(choices=ReportSeverity, null=True) # Null iff status = "NEW"
    priority = models.IntegerField(choices=ReportPriority, null=True) # Null iff status = "NEW"
    duplicate_of = models.ForeignKey("self", on_delete=models.CASCADE, null=True) # Null iff status != "DUPLICATE"
    title = models.CharField(max_length=50)
    description = models.TextField()
    reproduce_steps = models.TextField()
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    version = models.CharField(max_length=20, null=True)
    tester_id = models.CharField(max_length=20)
    tester_email = models.EmailField(null=True) # Set on creation, might be null
    assigned_to = models.ForeignKey("Employee", on_delete=models.SET_NULL, null=True) # Null iff not "ASSIGNED" / employee deleted

    def __str__(self):
        return f"{self.id:04d} | {self.status} : {self.title}"

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    report = models.ForeignKey("Report", on_delete=models.CASCADE)
    employee = models.ForeignKey("Employee", on_delete=models.SET_NULL, null=True) # Null iff employee is deleted
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.employee is None:
            return f"{self.id:04d} | Anonymous : {self.content}"
        return f"{self.id:04d} | {self.employee.email} : {self.content}"