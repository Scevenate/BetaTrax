# BetaTrax Server Setup Demo

## 1. Quick Start

### Local Server (Python manage.py + pip + virtual environment (assumed using anaconda))
1. Create a virtual environment with Python 3.13+, activate it.
```bash
conda create -n "3297demo" python=3.13
conda activate 3297demo
cd <YOUR_REPO_LOCATION>
```
2. Install dependencies:
   - `pip install django psycopg[binary]`
3. Run migrations:
   - `python manage.py makemigrations BetaTrax`
   - `python manage.py migrate`
4. Start server:
   - `python manage.py runserver`
5. Data persists in `./db.sqlite3`

### Remember to setup the database first as per the .md files then run the code!!!