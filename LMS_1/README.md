# Lead Management System (LMS)

A simple **Lead Management System** developed using Flask, SQLAlchemy, SQLite, Bootstrap, and vanilla JavaScript. The application uses Fetch API for smooth frontend-backend communication without page reloads.


## Features

- Public **lead submission** form (`/`) with client- and server-side validation.
- **Admin dashboard** (`/dashboard`) with search, status filter, and status updates.
- **REST API**: `POST /api/leads`, `GET /api/leads`, `PUT /api/leads/<id>`.
- **Automatic reply** text returned after each successful submission (plus an **OpenAI placeholder** in `app.py` for optional future integration).
- **Gunicorn**-ready entry point for **Render** (or any WSGI host).

## Authentication

This project uses a simple authentication system built with Flask.

Users can log in to access the dashboard using the following credentials:

```text
Username: admin
Password: admin123
```

When the login is successful, a user session is created and the user is redirected to the dashboard.

This authentication setup is created for learning and demonstration purposes. Currently, the username and password are hardcoded. In a production-level application, authentication should be implemented using a database, hashed passwords, and secure session management.

## Project layout

```text
project/
├── app.py                 # Flask app, validation, routes, auto-reply logic
├── models.py              # SQLAlchemy models
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   └── dashboard.html
├── static/
│   ├── style.css
│   └── script.js
├── instance/
│   └── leads.db           # created automatically on first run
├── postman/
│   └── LMS.postman_collection.json
└── README.md
```

## Database schema

SQLite file: `instance/leads.db` (created on startup if missing).

| Column          | Type     | Notes                                      |
|-----------------|----------|--------------------------------------------|
| `id`            | INTEGER  | Primary key, autoincrement                 |
| `name`          | VARCHAR  | Required                                   |
| `email`         | VARCHAR  | Required, indexed                          |
| `phone`         | VARCHAR  | Required                                   |
| `business_type` | VARCHAR  | Required                                   |
| `message`       | TEXT     | Required                                   |
| `status`        | VARCHAR  | `New`, `Contacted`, or `Closed` (indexed)  |
| `created_at`    | DATETIME | Set on insert                              |
| `updated_at`    | DATETIME | Updated when the row changes               |

Statuses are stored as short strings to keep the API and UI simple.

## Local setup

1. **Python 3.10+** recommended.

2. Create and activate a virtual environment (Windows PowerShell example):

   ```powershell
   cd path\to\LMS_1
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Run the development server:

   ```powershell
   flask --app app run
   ```

   Or:

   ```powershell
   python app.py
   ```

4. Open a browser:

   - Form: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
   - Dashboard: [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)

## API quick reference

| Method | Path                 | Description                                       |
|--------|----------------------|---------------------------------------------------|
| POST   | `/api/leads`         | Create a lead (JSON body). Returns `auto_reply`.  |
| GET    | `/api/leads`         | List leads.   `?q=` and `?status=`.               |
| PUT    | `/api/leads/<id>`    | Update `status` (`New` / `Contacted` / `Closed`). |

Example **POST** body:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "phone": "+1 (555) 010-2030",
  "business_type": "Technology",
  "message": "Interested in a demo."
}
```
## 📧 Email Automation

Email automation functionality is currently being implemented using Gmail SMTP and Python `smtplib`.

## Postman

Import `postman/LMS.postman_collection.json` into Postman. Set the `baseUrl` collection variable to your local or deployed origin (for example `https://your-service.onrender.com`).

## Production with Gunicorn

The Flask application object is named `app` (with an alias `application` for hosts that expect that name).

Typical local Gunicorn command:

```bash
gunicorn app:app
```

On **Render**, bind to the port provided by the platform:

```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

(If your host only accepts the word `application` as the callable, use `gunicorn app:application` instead.)

## Deploying to Render

1. Push this project to **GitHub** (root of the repo should contain `app.py` and `requirements.txt`).

2. In the [Render](https://render.com) dashboard, create a new **Web Service** connected to that repository.

3. Settings (example):

   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn --bind 0.0.0.0:$PORT app:app`

4. Add an environment variable:

   - `SECRET_KEY` — long random string for Flask session/signing (recommended for any production use).

5. Deploy. SQLite on Render’s **ephemeral filesystem** is fine for demos; for real production traffic, migrate to a managed database (Render Postgres, etc.).

## Security note

The dashboard is a **demo**: it has no login. In production, protect `/dashboard` and mutating APIs with authentication (for example Flask-Login, OAuth, or API keys behind a reverse proxy).


