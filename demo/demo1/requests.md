# 2 Ways to use python requests

## Way 1a. run in command line terminal

### Install dependency
Open any environment in another terminal and run `pip install requests`

### Request API demo (run in terminal)
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

### setup variable [using python shell]
```python
import requests

BASE_URL = 'http://127.0.0.1:8000'

# owner & developer login setup
owner_session = requests.Session()
owner_resp = owner_session.post(
    f'{BASE_URL}/login/',
    data={'email': 'owner@demo.com', 'password': 'ownerpassword'},
)
print('Owner login', owner_resp.status_code)
dev_session = requests.Session()
dev_resp = dev_session.post(
    f'{BASE_URL}/login/',
    data={'email': 'developer@demo.com', 'password': 'developerpassword'},
)
print('dev login', dev_resp.status_code)

# Add two reports
# time will be added automatically
resp1 = requests.post(
    f'{BASE_URL}/report/',
    data={
        'version': "0.9.0",
        'title': 'Unable to search',
        'description': 'Search button unresponsive after completing an initial search',
        'reproduce_steps': '1. Complete a search\n2. Modify search criteria\n3. Click Search button',
        'product': 1,
        'tester_id': 'Tester_1',
        'tester_email': 'icyreward@gmail.com',
    },
)
print('Created report1', resp1.status_code, resp1.text)

# open report 1
open_resp = owner_session.patch(
    f'{BASE_URL}/report/1/',
    json={'action': 'OPEN', 'severity': "MAJOR", 'priority': "HIGH"},
)
print('Open report', open_resp.status_code)
list_resp = owner_session.get(f'{BASE_URL}/report/?status=OPENED')
print('Opened reports', list_resp.status_code, list_resp.json())
# assign report 1
assign_resp = dev_session.patch(
    f'{BASE_URL}/report/1/',
    json={'action': 'ASSIGN'},
)
print('Assign report', assign_resp.status_code)
list_resp = dev_session.get(f'{BASE_URL}/report/?status=ASSIGNED')
print('Assigned reports', list_resp.status_code, list_resp.json())

# create report 2
resp2 = requests.post(
    f'{BASE_URL}/report/',
    data={
        'version': "0.9.0",
        'title': 'Poor readability in dark mode',
        'description': 'Text unclear in dark mode due to lack of contrast with background',
        'reproduce_steps': '1. Enable dark mode\n2. Display text',
        'product': 1,
        'tester_id': 'Tester_2',
    },
)

print('Created report2', resp2.status_code, resp2.text)
```

### Flow of demo
In the same shell:
1. Submit defect report (referred to as ‘target’ below).
```python
resp = requests.post(
    f'{BASE_URL}/report/',
    data={
        'version': 0.9.0,
        'title': 'Hit count incorrect',
        'description': 'Following a successful search, the hit count is different to the number of matches displayed',
        'reproduce_steps': '1. Enter search criteria that ensure at least one match\n2. Search\n3. Compare matches displayed with the number of hits reported.',
        'product': product.id,
        'tester_id': 'Tester_1',
        'tester_email': 'icyreward@gmail.com',
    },
)
print('Created target', resp.status_code, resp.text)
```

2. List report (i). [for product owner]
```python
list_resp = owner_session.get(f'{BASE_URL}/report/?status=NEW')
print('NEW reports', list_resp.status_code, list_resp.json())
```

3. View details of the target defect report [for product owner]
```python
list_resp = owner_session.get(f'{BASE_URL}/report/3')
print('Wanted target', list_resp.status_code, list_resp.json())
```

4. Accept the target defect report
```python
open_resp = owner_session.patch(
    f'{BASE_URL}/report/3/',
    json={'action': 'OPEN', 'severity': "MINOR", 'priority': "HIGH"},
)
print('Open report', open_resp.status_code)
```

5. List reports (ii). [for developer]
```python
list_resp = dev_session.get(f'{BASE_URL}/report/?status=OPENED')
print('OPENED reports', list_resp.status_code, list_resp.json())
```

6. View details of the target defect report [for developer]
```python
list_resp = dev_session.get(f'{BASE_URL}/report/3')
print('Wanted target', list_resp.status_code, list_resp.json())
```

7. As Developer, take responsibility for the target defect report
```python
assign_resp = dev_session.patch(
    f'{BASE_URL}/report/3/',
    json={'action': 'ASSIGN'},
)
print('Assign report', assign_resp.status_code)
```

8. List reports (iii). [for product owner]
```python
list_resp = owner_session.get(f'{BASE_URL}/report/?status=ASSIGNED')
print('ASSIGNED reports', list_resp.status_code, list_resp.json())
```

9. Set target defect report as Fixed [for developer]
```python
fix_resp = dev_session.patch(
    f'{BASE_URL}/report/3/',
    json={'action': 'FIX'},
)
print('Fix report', fix_resp.status_code)
```

10. List reports (iv) [for product owner]
```python
list_resp = owner_session.get(f'{BASE_URL}/report/?status=FIXED')
print('FIXED reports', list_resp.status_code, list_resp.json())
```

11. Close the target defect report as Resolved
```python
resolve_resp = owner_session.patch(
    f'{BASE_URL}/report/3/',
    json={'action': 'RESOLVE'},
)
print('Resolve report', resolve_resp.status_code)

list_resp = owner_session.get(f'{BASE_URL}/report/')
print('All reports', list_resp.status_code, list_resp.json())
```

## Way 1b: use requests.ipynb and run the code [need ipykernel python package]