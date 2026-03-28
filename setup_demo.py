#!/usr/bin/env python3
"""
BetaTrax Demo Setup Script

This script initializes the database with the necessary data for the Sprint 1 Demo:
- A Product (Prod_1)
- A Product Owner account
- A Developer account
- Two initial defect reports

Usage:
    python setup_demo.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from BetaTrax.models import Product, Employee, Report, ReportStatus, ReportSeverity, ReportPriority, EmployeeRole
from django.utils import timezone

def setup_demo():
    print("Creating Product")
    product, created = Product.objects.get_or_create(
        id=1,
        defaults={"name": "Prod_1"}
    )
    if created:
        print(f"Product created: {product.name} (ID: {product.id})")
    else:
        print(f"Product already exists: {product.name} (ID: {product.id})")
    
    print("\nCreating Product Owner account")
    try:
        po = Employee.objects.get(email="po@betatrax.com")
        print(f"Product Owner already exists")
    except Employee.DoesNotExist:
        po = Employee.objects.create_user(
            email="po@betatrax.com",
            password="password",
            product=product.id,
            role=EmployeeRole.PRODUCT_OWNER
        )
    
    print("Creating Developer account")
    try:
        dev = Employee.objects.get(email="dev@betatrax.com")
        print(f"Developer already exists")
    except Employee.DoesNotExist:
        dev = Employee.objects.create_user(
            email="dev@betatrax.com",
            password="password",
            product=product.id,
            role=EmployeeRole.DEVELOPER
        )
    
    print("Creating initial defect reports")
    report1, created1 = Report.objects.get_or_create(
        title="Unable to search",
        defaults={
            "product": product,
            "status": ReportStatus.ASSIGNED,
            "version": "0.9.0",
            "description": "Search button unresponsive after completing an initial search",
            "reproduce_steps": "1. Complete a search\n2. Modify search criteria\n3. Click Search button",
            "tester_id": "Tester_1",
            "tester_email": "icyreward@gmail.com",
            "severity": ReportSeverity.MAJOR,
            "priority": ReportPriority.HIGH,
            "assigned_to": dev,
            "created_at": timezone.datetime(2026, 3, 25, 10, 53)
        }
    )
    if created1:
        print(f"Report created: '{report1.title}' (ID: {report1.id}, Status: {report1.status})")
    else:
        print(f"Report already exists: '{report1.title}' (ID: {report1.id})")
    
    report2, created2 = Report.objects.get_or_create(
        title="Poor readability in dark mode",
        defaults={
            "product": product,
            "status": ReportStatus.NEW,
            "version": "0.9.0",
            "description": "Text unclear in dark mode due to lack of contrast with background",
            "reproduce_steps": "1. Enable dark mode\n2. Display text",
            "tester_id": "Tester_2",
            "tester_email": None,
            "created_at": timezone.datetime(2026, 3, 25, 20, 17)
        }
    )
    if created2:
        print(f"Report created: '{report2.title}' (ID: {report2.id}, Status: {report2.status})")
    else:
        print(f"Report already exists: '{report2.title}' (ID: {report2.id})")
    
    print("Demo setup completed")

if __name__ == "__main__":
    try:
        setup_demo()
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        import traceback
        traceback.print_exc()
