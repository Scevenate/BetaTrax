# run by `docker compose exec betatrax sh -lc "uv run manage.py shell < demo/demo2/setup.py"`

from django_tenants.utils import tenant_context
from Tenants.models import Tenant, Domain
from BetaTrax.models import Product, Employee


def get_or_create_tenant(schema_name, tenant_name, domain_name):
    tenant, created = Tenant.objects.get_or_create(
        schema_name=schema_name,
        defaults={"name": tenant_name},
    )

    domain, domain_created = Domain.objects.get_or_create(
        domain=domain_name,
        defaults={"tenant": tenant, "is_primary": True},
    )

    print(f"Tenant is created or fetched: schema={tenant.schema_name}, name={tenant.name}, domain={domain.domain}")
    return tenant

def insert_user(email, password, role, product):
    if product is not None:
        Employee.objects.create_user(
            email=email,
            password=password,
            role=role,
            product=product.id,
        )
        print(f"User ready: email={email}, password={password}, role={role}, product={product.id}")
    else:
        Employee.objects.create_user(
            email=email,
            password=password,
            role=role,
        )
        print(f"User ready: email={email}, password={password}, role={role}, product={product}")
    

print("---Tenant1---")
print("Create Tenant1")
tenant1 = get_or_create_tenant(
    schema_name="se1",
    tenant_name="SE Tenant 1",
    domain_name="se1.localhost",
)

with tenant_context(tenant1):
    print("Create product & users")
    product_1 = Product.objects.create(name='Prod_1')
    product_2 = Product.objects.create(name='Prod_2')


    insert_user("u1@t1", "pw", "PRODUCT_OWNER", product_1)
    insert_user("u2@t1", "pw", "DEVELOPER", product_1)
    insert_user("u3@t1", "pw", "PRODUCT_OWNER", product_2)
    insert_user("u4@t1", "pw", "DEVELOPER", product_2)
    insert_user("u5@t1", "pw", "DEVELOPER", product_2)
    insert_user("u6@t1", "pw", "DEVELOPER", None)
    insert_user("u7@t1", "pw", "DEVELOPER", None)
    insert_user("u8@t1", "pw", "DEVELOPER", None)

    Employee.objects.create_superuser(
        email="admin@admin.com",
        password="admin",
    )
    print("---Completed---\n")

print("---Tenant2---")
print("Create Tenant2")
tenant2 = get_or_create_tenant(
    schema_name="se2",
    tenant_name="SE Tenant 2",
    domain_name="se2.localhost",
)

with tenant_context(tenant2):
    print("Create product & users")
    product_1 = Product.objects.create(name="Prod_1")

    insert_user("u6@t2", "pw", "PRODUCT_OWNER", product_1)
    insert_user("u7@t2", "pw", "DEVELOPER", product_1)
    insert_user("u8@t2", "pw", "DEVELOPER", product_1)
    print("---Completed---\n")



print("Setup complete.")