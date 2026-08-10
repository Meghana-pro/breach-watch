# BreachWatch — Data Breach Early Warning Prototype

A beginner-friendly educational project built with Python, FastAPI, SQLite, HTML/CSS/JavaScript, pytest, Docker, and GitHub Actions.

## Important scope and safety notes

- The preloaded incident records are fictional demonstrations.
- Risk scores are produced by transparent rules, not a validated model of the probability that an account was compromised.
- A risk score is not proof that an account or individual is affected.
- The starter app does not connect to a real breach-intelligence provider by default.
- Never collect, store, or ask for passwords. Use only public/authorized incident information and follow each provider's terms.
- Do not use this prototype as the sole basis for security decisions.

## Features

- Dashboard with summary counts and incident cards.
- SQLite persistence.
- Explainable risk score and reasons.
- Add a fictional or appropriately sourced incident.
- Track whether follow-up actions have been completed.
- REST API and interactive docs at `/docs`.
- Pytest checks and GitHub Actions workflow.
- Dockerfile and Docker Compose configuration.

## Requirements

- Python 3.11 recommended.
- VS Code.
- Git (for GitHub steps).
- Docker Desktop is optional and only needed for the container step.

## Windows PowerShell setup

Open VS Code, choose **File → Open Folder**, and open the `breach_watch_project` folder.

Open **Terminal → New Terminal** and run each command separately:

```powershell
py --version
```

If Python is available, create a virtual environment:

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use this command for the current terminal only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start the web application:

```powershell
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000` in a browser. Keep the terminal running while using the site.

Interactive API documentation: `http://127.0.0.1:8000/docs`
Health check: `http://127.0.0.1:8000/api/health`

Stop the server by focusing the terminal and pressing **Ctrl+C**.

## Test the application

Open a second VS Code terminal, activate the virtual environment, and run:

```powershell
pytest -q
```

Expected result: all tests pass. If a test fails, read the first error message and check that the dependencies installed successfully.

## Project structure

```text
breach_watch_project/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   └── risk.py
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
│   └── test_app.py
├── sample_data/
│   └── README.md
├── .github/workflows/tests.yml
├── data/                  # Created automatically; local SQLite DB
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check whether the app is running |
| GET | `/api/summary` | Dashboard totals |
| GET | `/api/incidents` | List incident records |
| POST | `/api/incidents` | Score and save an incident |
| PATCH | `/api/incidents/{id}/action` | Mark follow-up complete or reopen it |
| GET | `/docs` | Interactive API documentation |

## Test the API manually

Start the server and open `http://127.0.0.1:8000/docs`. Expand `GET /api/health`, click **Try it out**, then **Execute**. Repeat with `GET /api/incidents`.

To create a test record, use `POST /api/incidents` and a body like:

```json
{
  "organization": "Example Training Company",
  "title": "Fictional credential exposure",
  "description": "Training example only; not a real incident.",
  "source_name": "Manual demo",
  "source_url": "",
  "incident_date": "2026-01-15",
  "data_types": ["email_addresses", "passwords"]
}
```

## GitHub setup

1. Create a new empty repository on GitHub, for example `breach-watch`.
2. In VS Code terminal, run:

```powershell
git init
git add .
git commit -m "Build BreachWatch prototype"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/breach-watch.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your own GitHub username. Do not include API keys or `.env` files in GitHub.

GitHub Actions will run the tests after a push or pull request. Open the repository's **Actions** tab to see the result.

## Docker

Make sure Docker Desktop is running, then from the project root run:

```powershell
docker compose up --build
```

Open `http://127.0.0.1:8000`. Stop the container with **Ctrl+C**, then run:

```powershell
docker compose down
```

The named Docker volume keeps the database between container restarts.

## Connecting a real breach-intelligence provider

The starter deliberately uses fictional local records. Before adding a real source:

1. Choose a provider that explicitly permits your intended use.
2. Read its current API documentation, authentication rules, rate limits, attribution rules, and data-retention conditions.
3. Create an API key only if the provider requires one; keep it in an environment variable or the hosting provider's secret manager.
4. Implement a separate provider adapter that maps the provider's response to the incident fields used by this app.
5. Store the original source name, URL, and provider-reported date.
6. Deduplicate by the provider's stable incident identifier or canonical URL.
7. Handle rate limits, timeouts, missing fields, and provider errors.
8. Add mocked tests for the adapter before enabling scheduled polling.
9. Never scrape a service or access non-public data in violation of its terms.

Provider response formats differ, so there is no safe universal API call that works with every provider. Do not add a real integration until you have chosen a provider and checked its documentation.

## Deployment checklist

1. Push the tested project to GitHub.
2. Choose a host that supports Python web services or Docker.
3. Configure the start command: `uvicorn main:app --host 0.0.0.0 --port $PORT` if the host provides a `PORT` environment variable.
4. Configure persistent storage for SQLite, or use a managed database if the host's filesystem is ephemeral or the app needs concurrent production use.
5. Add secrets through the host's environment-variable settings; never commit them.
6. Deploy and verify `/api/health`, `/docs`, and the dashboard.
7. Confirm the provider's terms permit the deployed use before enabling real data collection.

## Suggested next improvements

- Authentication and per-user access controls.
- Managed database for production.
- Provider-specific data connector and deduplication.
- Scheduled polling and alert delivery.
- Audit logging and retention controls.
- A trained ML model only after obtaining a lawful, representative, labeled dataset and evaluating it on held-out data.
