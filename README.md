# Assignment & Deadline Tracker

A Django web application that helps students record assignments, track deadlines
and see what is pending, due soon or overdue on a single dashboard.

**Stack:** Python · Django · SQLite · HTML · CSS · GitHub

## Features
- Create, read, update and delete (CRUD) assignments
- Subjects (courses) that assignments belong to - one-to-many relationship
- Dashboard cards: total, pending, due soon, overdue, completed + progress bar
- Filter by subject, status, priority and search by keyword
- Automatic "overdue" / "due today" / "N days left" labels
- One-click "Done" / "Undo" button
- Form validation (title length, no past deadline for new assignments, unique subject)
- Delete confirmation page, flash messages, responsive layout (table turns into cards on phones), dark mode
- Django admin panel for managing data
- Automated tests (models, forms, views)

## Project structure
```
assignment_deadline_tracker/
├── manage.py
├── requirements.txt
├── deadline_tracker/        # project settings, root urls, wsgi
└── tracker/                 # the app
    ├── models.py            # Subject, Assignment
    ├── forms.py             # ModelForms + validation
    ├── views.py             # dashboard, CRUD, toggle, subjects
    ├── urls.py
    ├── admin.py
    ├── tests.py
    ├── migrations/
    ├── management/commands/seed_data.py   # sample data
    ├── templates/tracker/   # base, dashboard, forms, subjects
    └── static/tracker/style.css
```

## Run locally
```bash
# 1. (optional) create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# 2. install Django
pip install -r requirements.txt

# 3. create the SQLite database tables
python manage.py migrate

# 4. (optional) load demo data for your screenshots
python manage.py seed_data

# 5. (optional) create an admin login for /admin
python manage.py createsuperuser

# 6. start the server
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Run the tests
```bash
python manage.py test
```

## Push to GitHub
```bash
git init
git add .
git commit -m "Assignment & Deadline Tracker using Django"
git branch -M main
git remote add origin https://github.com/<your-username>/assignment-deadline-tracker.git
git push -u origin main
```

## Deploy on PythonAnywhere (free)
1. Upload the project (or `git clone` it) in a PythonAnywhere Bash console.
2. Create a virtualenv and `pip install -r requirements.txt`.
3. Web tab → *Add a new web app* → *Manual configuration* → pick your Python version.
4. Set **Source code** and **Virtualenv** paths. In the WSGI file use:
   ```python
   import os, sys
   path = "/home/<username>/assignment_deadline_tracker"
   if path not in sys.path:
       sys.path.insert(0, path)
   os.environ["DJANGO_SETTINGS_MODULE"] = "deadline_tracker.settings"
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
5. In the console run `python manage.py migrate` and `python manage.py collectstatic`.
6. In the Web tab add a **Static files** entry: URL `/static/` → directory `/home/<username>/assignment_deadline_tracker/staticfiles`.
7. Set the env vars `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=False`, then click **Reload**.

## Data model
| Subject | | Assignment | |
|---|---|---|---|
| id | PK | id | PK |
| name | unique | title | |
| code | optional | subject | FK → Subject |
| | | description | |
| | | due_date | |
| | | priority | low / medium / high |
| | | status | pending / in_progress / completed |
| | | completed_on | auto-set |
| | | created_at | auto |
