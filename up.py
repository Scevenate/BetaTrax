import subprocess
import sys
import os

def manage(*args):
    result = subprocess.run([sys.executable, 'manage.py', *args])
    if result.returncode != 0:
        sys.exit(result.returncode)

def set_default_tenant():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    import django
    django.setup()
    from Tenants.models import Tenant, Domain

    schema_name = os.getenv("DEFAULT_TENANT_SCHEMA", "default")
    tenant_name = os.getenv("DEFAULT_TENANT_NAME", "default")
    domain_name = os.getenv("DEFAULT_TENANT_DOMAIN", "localhost")

    tenant, created = Tenant.objects.get_or_create(
        schema_name=schema_name,
        defaults={"name": tenant_name},
    )
    if not created and tenant.name != tenant_name:
        tenant.name = tenant_name
        tenant.save(update_fields=["name"])

    Domain.objects.get_or_create(
        domain=domain_name,
        defaults={"tenant": tenant, "is_primary": True},
    )

manage('makemigrations', 'Tenants')
manage('makemigrations', 'BetaTrax')
manage('migrate_schemas', '--shared')
if os.getenv("SET_DEFAULT_TENANT") == "True":
    set_default_tenant()
manage('migrate_schemas', '--tenant')
manage('collectstatic', '--noinput')
subprocess.run(['gunicorn', '--bind', f"0.0.0.0:{os.getenv('DJANGO_PORT')}", 'project.wsgi:application'])