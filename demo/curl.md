# curl API Demo

## Install curl

- Windows (PowerShell):
  ```powershell
  winget install curl
  ```
- Or with Chocolatey:
  ```powershell
  choco install curl
  ```
- macOS:
  ```bash
  brew install curl
  ```
- Linux:
  ```bash
  sudo apt install curl
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

curl -c owner_cookies.txt -d "email=owner@demo.com&password=ownerpassword" "$BASE_URL/login/"
curl -c dev_cookies.txt -d "email=developer@demo.com&password=developerpassword" "$BASE_URL/login/"
```

```bash
curl -b owner_cookies.txt -X POST "$BASE_URL/report/" \
  -d "version=0.9.0" \
  -d "title=Unable to search" \
  -d "description=Search button unresponsive after completing an initial search" \
  -d "reproduce_steps=1. Complete a search\n2. Modify search criteria\n3. Click Search button" \
  -d "product=1" \
  -d "tester_id=Tester_1" \
  -d "tester_email=icyreward@gmail.com"

curl -b owner_cookies.txt -X PATCH "$BASE_URL/report/1/" \
  -H "Content-Type: application/json" \
  -d '{"action": "OPEN", "severity": "MAJOR", "priority": "HIGH"}'

curl -b owner_cookies.txt "$BASE_URL/report/?status=OPENED"
curl -b dev_cookies.txt -X PATCH "$BASE_URL/report/1/" \
  -H "Content-Type: application/json" \
  -d '{"action": "ASSIGN"}'

curl -b dev_cookies.txt "$BASE_URL/report/?status=ASSIGNED"

curl -b owner_cookies.txt -X POST "$BASE_URL/report/" \
  -d "version=0.9.0" \
  -d "title=Poor readability in dark mode" \
  -d "description=Text unclear in dark mode due to lack of contrast with background" \
  -d "reproduce_steps=1. Enable dark mode\n2. Display text" \
  -d "product=1" \
  -d "tester_id=Tester_2"
```

## Flow of demo

In the same shell:
1. Submit defect report (referred to as ‘target’ below).
```bash
curl -b owner_cookies.txt -X POST "$BASE_URL/report/" \
  -d "version=0.9.0" \
  -d "title=Hit count incorrect" \
  -d "description=Following a successful search, the hit count is different to the number of matches displayed" \
  -d "reproduce_steps=1. Enter search criteria that ensure at least one match\n2. Search\n3. Compare matches displayed with the number of hits reported." \
  -d "product=1" \
  -d "tester_id=Tester_1" \
  -d "tester_email=icyreward@gmail.com"
```

2. List report (i). [for product owner]
```bash
curl -b owner_cookies.txt "$BASE_URL/report/?status=NEW"
```

3. View details of the target defect report [for product owner]
```bash
curl -b owner_cookies.txt "$BASE_URL/report/3"
```

4. Accept the target defect report
```bash
curl -b owner_cookies.txt -X PATCH "$BASE_URL/report/3/" \
  -H "Content-Type: application/json" \
  -d '{"action": "OPEN", "severity": "MINOR", "priority": "HIGH"}'
```

5. List reports (ii). [for developer]
```bash
curl -b dev_cookies.txt "$BASE_URL/report/?status=OPENED"
```

6. View details of the target defect report [for developer]
```bash
curl -b dev_cookies.txt "$BASE_URL/report/3"
```

7. As Developer, take responsibility for the target defect report
```bash
curl -b dev_cookies.txt -X PATCH "$BASE_URL/report/3/" \
  -H "Content-Type: application/json" \
  -d '{"action": "ASSIGN"}'
```

8. List reports (iii). [for product owner]
```bash
curl -b owner_cookies.txt "$BASE_URL/report/?status=ASSIGNED"
```

9. Set target defect report as Fixed [for developer]
```bash
curl -b dev_cookies.txt -X PATCH "$BASE_URL/report/3/" \
  -H "Content-Type: application/json" \
  -d '{"action": "FIX"}'
```

10. List reports (iv) [for product owner]
```bash
curl -b owner_cookies.txt "$BASE_URL/report/?status=FIXED"
```

11. Close the target defect report as Resolved
```bash
curl -b owner_cookies.txt -X PATCH "$BASE_URL/report/3/" \
  -H "Content-Type: application/json" \
  -d '{"action": "RESOLVE"}'

curl -b owner_cookies.txt "$BASE_URL/report/"
```

## Way 1b: use curl.ipynb and run the code [need ipykernel python package]
