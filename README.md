# Suffolkcoins

The website of Suffolk Coins, a coin dealer: a landing page with a banner carousel, a **live inventory list** (a Google Sheet exported as a PDF), and a contact form whose messages are stored for the owner to answer. A small Django site with an admin.

(The old README described a "cryptocurrency platform" with secure transactions and live market data. The code never did any of that.)

## What it does

| Page | |
|---|---|
| `/` | Landing page: contact details, banner carousel, contact form |
| `/inventory/` | The inventory Google Sheet exported as a PDF and shown in the browser. Cached for 5 minutes; the last good copy is shown if Google is unreachable |
| `/contact/` | Receives the form (POST only) and saves it |
| `/admin/` | Read the messages and tick them when handled; upload PDFs (Jazzmin theme) |

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) (Python 3.13).

```bash
uv sync
cp .env.example .env              # set DEBUG=true for local work
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver  # http://127.0.0.1:8000
```

### The live inventory list

The list is exported with a Google **service account**:

1. Create a service account in Google Cloud and a JSON key for it.
2. Share the inventory Google Sheet with the service account's e-mail address (Viewer is enough).
3. Set `INVENTORY_SHEET_ID` (the long id in the sheet's URL) and `GOOGLE_APPLICATION_CREDENTIALS` (the path of the key file, **outside the repository**).

Without them `/inventory/` answers 503 and the rest of the site works. The app only asks for read access to Drive (it used to ask for full access).

## Configuration

Environment variables, or a local `.env` read by `manage.py`. An empty value counts as unset. [`.env.example`](./.env.example) lists them all.

| Variable | Default | |
|---|---|---|
| `SECRET_KEY` | none | **Required** unless `DEBUG=true` |
| `ALLOWED_HOSTS` | none (localhost when `DEBUG=true`) | Comma-separated host names. **Set it in production** or every request is refused |
| `DEBUG` | `false` | Local development only |
| `HTTPS_ONLY` | `true` unless `DEBUG` | Redirect to HTTPS, secure cookies, HSTS (expects a TLS-terminating proxy that sets `X-Forwarded-Proto`) |
| `HSTS_SECONDS`, `CSRF_TRUSTED_ORIGINS` | `3600`, empty | |
| `DATABASE_PATH`, `STATIC_ROOT`, `MEDIA_ROOT` | `./db.sqlite3`, `./staticfiles`, `./media` | |
| `GOOGLE_APPLICATION_CREDENTIALS`, `INVENTORY_SHEET_ID` | none | See above |
| `INVENTORY_CACHE_SECONDS` | `300` | How long the exported PDF is reused |
| `LOG_LEVEL` | `INFO` | Logs go to the console |

## Project structure

```
suffolkcoins/    settings (environment driven), urls, wsgi/asgi, settings_test
inventory/       models (ContactMessage, Inventory), views, forms, admin, drive.py (the Google export)
templates/       base, index and the partials (navbar, carousel, form, footer)
static/          banners, logo, css/site.css (built, committed), js/carousel.js
assets/site.css  Tailwind entry point;  package.json builds static/css/site.css
tests/           pytest-django
Dockerfile  pyproject.toml  uv.lock
```

The stylesheet is compiled with Tailwind and committed, so deploying needs no Node.js. After changing templates run `npm ci && npm run build:css` and commit the result (CI checks it is up to date).

## Testing

```bash
uv run pytest -q                          # 66 tests, 95% coverage
uv run ruff check . && uv run ruff format --check .
uv run bandit -q -r inventory suffolkcoins manage.py
```

## Deployment

```bash
docker build -t suffolkcoins .
docker run -d -p 8000:8000 -v suffolkcoins-data:/data \
  -e SECRET_KEY=... -e ALLOWED_HOSTS=example.com \
  -e INVENTORY_SHEET_ID=... -e GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/google.json \
  -v /path/to/service-account.json:/run/secrets/google.json:ro \
  suffolkcoins
```

The image runs as a non-root user, applies migrations on start and serves static files itself (WhiteNoise); put TLS in front. The database and uploaded files live in the `/data` volume. Back that volume up: it holds your customers' messages (names and phone numbers).

## Versions

[VERSIONS.md](./VERSIONS.md). What changed and what needs your attention (**a Google key in the git history**): [work-done.md](./work-done.md).

## License

MIT, see [LICENSE](./LICENSE).
