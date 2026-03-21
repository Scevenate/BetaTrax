from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class EmployeeManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        return self.create_user(email, password, **extra_fields)

class EmployeeRole(models.TextChoices):
    PRODUCT_OWNER = "PRODUCT_OWNER"
    DEVELOPER = "DEVELOPER"

class Employee(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=EmployeeRole, null=True) # Not strictly required
    product = models.ForeignKey("Product", on_delete=models.SET_NULL, null=True) # Not strictly required
    objects = EmployeeManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

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
    OPEN = "OPEN"
    REJECTED = "REJECTED" #DEAD STATE
    DUPLICATE = "DUPLICATE" # DEAD STATE
    # OPEN TO:
    ASSIGNED = "ASSIGNED"
    # ASSIGNED TO:
    FIXED = "FIXED"
    CANNOT_REPRODUCE = "CANNOT_REPRODUCE" # DEAD STATE
    # FIXED TO:
    REOPENED = "REOPENED" # MAY BE REASSIGNED
    RESOLVED = "RESOLVED" # DEAD STATE

class ReportSeverity(models.TextChoices):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    LOW = "LOW"

class ReportPriority(models.TextChoices):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Report(models.Model):
    id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=20, choices=ReportStatus)
    severity = models.CharField(max_length=20, choices=ReportSeverity, null=True) # Null iff status = "NEW"
    priority = models.CharField(max_length=20, choices=ReportPriority, null=True) # Null iff status = "NEW"
    duplicate_of = models.ForeignKey("self", on_delete=models.CASCADE, null=True) # Null iff status != "DUPLICATE"
    title = models.CharField(max_length=50)
    description = models.TextField()
    tester_email = models.EmailField(null=True) # Set on creation, might be null
    assigned_to = models.ForeignKey("Employee", on_delete=models.SET_NULL, null=True) # Null iff have not reached "ASSIGNED" or employee is deleted

    def __str__(self):
        return f"{self.id:04d} | {self.status} : {self.title}"

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    report = models.ForeignKey("Report", on_delete=models.CASCADE)
    employee = models.ForeignKey("Employee", on_delete=models.SET_NULL, null=True) # Null iff employee is deleted
    content = models.TextField()

    def __str__(self):
        if self.employee is None:
            return f"{self.id:04d} | Anonymous : {self.content}"
        return f"{self.id:04d} | {self.employee.email} : {self.content}"