# Drakkar Shipping

Vulnerable web application for the Aktraen cybersecurity training mission "Rien de complique". This is a shipping company website built with Flask that contains multiple **information disclosure** vulnerabilities for trainees to discover.

## Vulnerabilities

- **Verbose HTTP headers**: `X-Powered-By: Flask`, `X-Server-Version`, `X-Debug-Mode`
- **Exposed `.git/` directory**: accessible at `/.git/` with config, commit history, and a source backup containing hardcoded secrets (Flask secret key, database credentials, SMTP password)
- **Flask debug mode**: `DEBUG=True` causes full stack traces with file paths, variables, and code context on unhandled exceptions
- **Undocumented admin endpoints**: `/admin/`, `/admin/users`, `/admin/logs`
- **Debug endpoint**: `/debug` returns application configuration, environment variables, and registered routes

## Credentials

| Username | Password | Role |
|----------|----------|------|
| `audit` | `DK!audit2026` | Auditor |
| `admin` | `DK!superadmin#2026` | Admin |

## Running Locally

```bash
docker compose up -d
```

The app listens on port 80 (mapped from container port 5000).

## Triggering Vulnerabilities

- **Headers**: inspect any HTTP response headers
- **Git leak**: browse to `/.git/` or `/.git/config`, `/.git/source_backup/app.py`
- **Stack traces**: submit a tracking number containing special characters (e.g., `test'or`)
- **Admin panel**: navigate to `/admin/` while logged in
- **Debug info**: navigate to `/debug`

## Stack

- Python 3.12 / Flask 3.1
- SQLite
- Docker
