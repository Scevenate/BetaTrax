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
    Employee.objects.create_user(
        email=email,
        password=password,
        role=role,
        product=product.id,
    )
    print(f"User ready: email={email}, password={password}, role={role}, product={product.id}")

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

    insert_user("user_1_po@tenant1.com", "user_1_pw", "PRODUCT_OWNER", product_1)
    insert_user("user_2_dev@tenant1.com", "user_2_pw", "DEVELOPER", product_1)
    insert_user("user_3@tenant1.com", "user_3_pw", "DEVELOPER", product_1)
    insert_user("user_4@tenant1.com", "user_4_pw", "DEVELOPER", product_1)
    insert_user("user_5@tenant1.com", "user_5_pw", "DEVELOPER", product_1)
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

    insert_user("user_6_po@tenant2.com", "user_6_pw", "PRODUCT_OWNER", product_1)
    insert_user("user_7_dev@tenant2.com", "user_7_pw", "DEVELOPER", product_1)
    insert_user("user_8_dev@tenant2.com", "user_8_pw", "DEVELOPER", product_1)
    print("---Completed---\n")



print("Setup complete.")