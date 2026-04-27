# HTTPie API Demo

## Install HTTPie

- Using Python / pip:
  ```bash
  pip install httpie
  ```
- Confirm installation:
  ```bash
  http --version
  ```

## Request API demo (run in terminal)

### Setup database

1. Start Django shell:
   - `python manage.py shell`
2. In shell:
   ```python
   from BetaTrax.models import Product, Employee, Report

   # create product
   product = Product.objects.create(name='Prod_1')
   print(f"Added Product: name={product.name}, id={1}")

   # linked to 1 owner and developer
   owner = Employee.objects.create_user(
       email='owner@demo.com',
       password='ownerpassword',
       role='PRODUCT_OWNER',
       product=product.id,
   )
   print(f"Added Product Owner: email={owner.email}, id={owner.id}, role={owner.role}, product={owner.product_id}")
   developer = Employee.objects.create_user(
       email='developer@demo.com',
       password='developerpassword',
       role='DEVELOPER',
       product=product.id,
   )
   print(f"Added Developer: email={developer.email}, id={developer.id}, role={developer.role}, product={developer.product_id}")
   ```
3. Exit
   - `exit`

### setup variable [using shell]

```bash
BASE_URL=http://127.0.0.1:8000

http --session=owner_session POST $BASE_URL/login/ email=owner@demo.com password=ownerpassword
http --session=dev_session POST $BASE_URL/login/ email=developer@demo.com password=developerpassword
```

```bash
http --session=owner_session POST $BASE_URL/report/ \
  version=0.9.0 \
  title='Unable to search' \
  description='Search button unresponsive after completing an initial search' \
  reproduce_steps='1. Complete a search\n2. Modify search criteria\n3. Click Search button' \
  product:=1 \
  tester_id=Tester_1 \
  tester_email=icyreward@gmail.com

http --session=owner_session PATCH $BASE_URL/report/1/ action=OPEN severity=MAJOR priority=HIGH
http --session=owner_session GET "$BASE_URL/report/?status=OPENED"
http --session=dev_session PATCH $BASE_URL/report/1/ action=ASSIGN
http --session=dev_session GET "$BASE_URL/report/?status=ASSIGNED"

http --session=owner_session POST $BASE_URL/report/ \
  version=0.9.0 \
  title='Poor readability in dark mode' \
  description='Text unclear in dark mode due to lack of contrast with background' \
  reproduce_steps='1. Enable dark mode\n2. Display Text' \
  product:=1 \
  tester_id=Tester_2
```

## Flow of demo

In the same shell:
1. Submit defect report (referred to as ‘target’ below).
```bash
http --session=owner_session POST $BASE_URL/report/ \
  version=0.9.0 \
  title='Hit count incorrect' \
  description='Following a successful search, the hit count is different to the number of matches displayed' \
  reproduce_steps='1. Enter search criteria that ensure at least one match\n2. Search\n3. Compare matches displayed with the number of hits reported.' \
  product:=1 \
  tester_id=Tester_1 \
  tester_email=icyreward@gmail.com
```

2. List report (i). [for product owner]
```bash
http --session=owner_session GET "$BASE_URL/report/?status=NEW"
```

3. View details of the target defect report [for product owner]
```bash
http --session=owner_session GET $BASE_URL/report/3
```

4. Accept the target defect report
```bash
http --session=owner_session PATCH $BASE_URL/report/3/ action=OPEN severity=MINOR priority=HIGH
```

5. List reports (ii). [for developer]
```bash
http --session=dev_session GET "$BASE_URL/report/?status=OPENED"
```

6. View details of the target defect report [for developer]
```bash
http --session=dev_session GET $BASE_URL/report/3
```

7. As Developer, take responsibility for the target defect report
```bash
http --session=dev_session PATCH $BASE_URL/report/3/ action=ASSIGN
```

8. List reports (iii). [for product owner]
```bash
http --session=owner_session GET "$BASE_URL/report/?status=ASSIGNED"
```

9. Set target defect report as Fixed [for developer]
```bash
http --session=dev_session PATCH $BASE_URL/report/3/ action=FIX
```

10. List reports (iv) [for product owner]
```bash
http --session=owner_session GET "$BASE_URL/report/?status=FIXED"
```

11. Close the target defect report as Resolved
```bash
http --session=owner_session PATCH $BASE_URL/report/3/ action=RESOLVE
http --session=owner_session GET $BASE_URL/report/
```

## Way 1b: use httpie.ipynb and run the code [need ipykernel python package]
