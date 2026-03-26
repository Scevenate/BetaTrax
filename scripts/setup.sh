#!/bin/bash
cd "$(dirname "$0")" || exit 1
if [ -f setup ]; then
    echo "Project already setup. Delete scripts/setup if you're sure."
    exit 1
fi
touch setup
cd "$(dirname "$0")/.." || exit 1

read -r -p "Superuser email: " superuser_email
while ! [[ $superuser_email =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$ ]]; do
    echo "Invalid email."
    read -r -p "Superuser email: " superuser_email
done
read -r -s -p "Superuser password: " superuser_password
while [[ -z $superuser_password ]]; do
    echo "Password cannot be empty."
    read -r -s -p "Superuser password: " superuser_password
done
uv sync
uv run manage.py makemigrations BetaTrax
uv run manage.py makemigrations
uv run manage.py migrate
echo "Employee.objects.create_superuser(
    email='$superuser_email',
    password='$superuser_password',
    role='PRODUCT_OWNER',
    product=Product.objects.create(name='Initial Product'),
);" | uv run manage.py shell

echo "Setup complete."