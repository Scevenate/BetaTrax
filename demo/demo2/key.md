# SE1 Demo JSON Key

Use these payloads on `se1.localhost` only.

## Login POST bodies

`u1`
```json
{
	"email": "u1@t1",
	"password": "pw"
}
```

`u2`
```json
{
	"email": "u2@t1",
	"password": "pw"
}
```

`u3`
```json
{
	"email": "u3@t1",
	"password": "pw"
}
```

`u4`
```json
{
	"email": "u4@t1",
	"password": "pw"
}
```

`u5`
```json
{
	"email": "u5@t1",
	"password": "pw"
}
```

`u6`
```json
{
	"email": "u6@t1",
	"password": "pw"
}
```

`u7`
```json
{
	"email": "u7@t1",
	"password": "pw"
}
```

## Report create POST bodies

`R1` - first demo report
```json
{
	"version": "0.9.0",
	"title": "Unable to search (DR0)",
	"description": "Search button unresponsive after completing an initial search",
	"reproduce_steps": "1. Complete a search\n2. Modify search criteria\n3. Click Search button",
	"product": 1,
	"tester_id": "Tester_1",
	"tester_email": "icyreward@gmail.com "
}
```

`R2`
```json
{
	"version": "0.9.0",
	"title": "DR1",
	"description": "Desc",
	"reproduce_steps": "Step",
	"product": 1,
	"tester_id": "Tester_2",
	"tester_email": "betatraxusers@gmail.com"
}
```

`R3`
```json
{
	"version": "0.9.0",
	"title": "DR2",
	"description": "Desc",
	"reproduce_steps": "Step",
	"product": 2,
	"tester_id": "Tester_1",
	"tester_email": "icyreward@gmail.com"
}
```

`R4`
```json
{
	"version": "0.9.0",
	"title": "DR3",
	"description": "Desc",
	"reproduce_steps": "Step",
	"product": 2,
	"tester_id": "Tester_2",
	"tester_email": "betatraxusers@gmail.com"
}
```

## Report action / status change JSON bodies

`OPEN` on report 1 by PO user `u1`
```json
{
	"action": "OPEN",
	"severity": "MAJOR",
	"priority": "HIGH"
}
```

`ASSIGN` on report 1 by dev user `u2`
```json
{
	"action": "ASSIGN"
}
```

`FIX` on report 1 by the assigned dev
```json
{
	"action": "FIX"
}
```

`CANNOT_REPRODUCE` on report 1 by the assigned dev
```json
{
	"action": "CANNOT_REPRODUCE"
}
```

`REOPEN` on report 1 by PO user after a fix
```json
{
	"action": "REOPEN"
}
```

`RESOLVE` on report 1 by PO user after a fix
```json
{
	"action": "RESOLVE"
}
```

`REJECT` on a new report by PO user
```json
{
	"action": "REJECT"
}
```

`DUPLICATE` on a new report by PO user
```json
{
	"action": "DUPLICATE",
	"duplicate_of": 1
}
```

## Employee product change JSON body

PATCH your own employee record with the new product id:
```json
{
	"product": 2
}
```

Example endpoint: `/employee/<employee_id>/`

## admin site
AC: admin@admin.com
PW: admin