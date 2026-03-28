import subprocess
import sys
import os

def manage(*args):
    result = subprocess.run([sys.executable, 'manage.py', *args])
    if result.returncode != 0:
        sys.exit(result.returncode)

manage('makemigrations', 'BetaTrax')
manage('makemigrations')
manage('migrate')
subprocess.run(['gunicorn', '--bind', f"0.0.0.0:{os.getenv('DJANGO_PORT')}", 'project.wsgi:application'])