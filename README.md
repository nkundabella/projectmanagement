# Trackera — Project Management System

A Django-based project management application with full CRUD for projects, tasks, and time logs. Integrates the [`errorutils`](https://test.pypi.org/project/the-error-utils/) package for robust error handling, numeric validation, and safe arithmetic throughout the codebase.

## Tech Stack

- **Backend**: Django (Python)
- **Database**: SQLite (development) / PostgreSQL (production via `psycopg2-binary`)
- **Error Handling & Validation**: [`errorutils`](https://test.pypi.org/project/the-error-utils/) (`the-error-utils`)

## Features

- **User authentication** — register, login, logout
- **Projects** — create, view, edit, delete with budget tracking and status/priority filters
- **Tasks** — full CRUD with assignment, due dates, and status workflows
- **Time Logs** — log hours worked per task; validated strictly via `errorutils`
- **Dashboard** — live metrics (totals, completion rates, budget summaries) computed with `errorutils.ops`
- **`errorutils` integration** — used across models, forms, services, and views for:
  - `validate_number` — guards all numeric fields (budget, hours, etc.)
  - `check_not_none` — enforces required FK relationships
  - `log_error` — logs failures without crashing request cycles
  - `safe_call` — wraps metric calculations with automatic fallbacks
  - `ops.add` / `ops.multiply` / `ops.average` — validated arithmetic for project metrics

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd projectmanagement
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

> `the-error-utils` is hosted on TestPyPI — install it first, then the rest:

```bash
pip install -i https://test.pypi.org/simple/ the-error-utils==0.2.0
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. (Optional) Seed demo data

```bash
python manage.py seed_data
```

Demo accounts created:
| Username | Password     | Role          |
|----------|--------------|---------------|
| admin    | admin123     | Superuser     |
| sarah    | password123  | Project Manager |
| alex     | password123  | Developer     |

### 6. Run the development server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Running Tests

```bash
python manage.py test trackera
```

Tests cover:
- `errorutils` integration (validate_number, check_not_none, ops)
- Model validation and inheritance
- Business logic services (metrics, time logging)
- Security and authorization (permission checks)

## Project Structure

```
projectmanagement/
├── manage.py
├── requirements.txt
├── .gitignore
├── db.sqlite3            # local dev DB (gitignored)
├── projectmanagement/    # Django settings & URL config
├── trackera/             # Main app (models, views, forms, services, tests)
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py
│   ├── migrations/
│   ├── models.py         # errorutils used for validation in clean()
│   ├── forms.py          # errorutils.validate_number in form cleaners
│   ├── views.py          # errorutils.log_error and ValidationError handling
│   ├── services.py       # errorutils.ops for metrics aggregation
│   └── tests.py          # Full test suite including errorutils integration
├── camellia/             # Secondary app (restaurant landing pages)
├── static/               # CSS, JS assets
└── templates/            # HTML templates
```

## errorutils Package

`errorutils` is a lightweight, zero-dependency Python utility package for safe error handling and numeric validation.

- **PyPI name**: `the-error-utils`
- **Import name**: `errorutils`
- **Install**: `pip install -i https://test.pypi.org/simple/ the-error-utils==0.2.0`

## License

MIT
