# Work done: suffolkcoins

Branch: `chore/modernize` (local, not pushed). Date: 2026-11-02.

## What was there
A small Django 4.2 site (about 620 lines of code): a landing page with a banner carousel, an inventory page that returns a Google Sheet as a PDF, an unused `Inventory` upload model, and a "live chat" form. 225 tracked files, **191 of them collected static files (`staticfiles/`)**, `credentials.json`, three dependency files listing 49 packages (about three quarters unused), no tests, and a README that described a cryptocurrency platform the code never was.

## Credentials: the most important part of this report
- **`credentials.json` is a Google Cloud service-account key** (a `private_key`, `private_key_id` and `client_email`; its contents were not read or printed). It was committed and read from the source folder at run time. **One commit in the history holds the private key and it is still there**, so anyone who can read this repository can act as that service account and read every Google file shared with it.
  - Now: untracked (the file is still on your disk), ignored, excluded from Docker images, and no longer read from the project folder.
  - **Rotate it:** in Google Cloud delete that key (IAM > Service accounts > Keys), create a new one, keep it outside the repository, and set `GOOGLE_APPLICATION_CREDENTIALS`. Removing it from history means rewriting history and force-pushing, which you must do yourself.
- **The Django `SECRET_KEY` was a literal in `settings.py`** (one commit in the history) and `DEBUG = True` was hard-coded, so a live site would have shown debug pages and used a forgeable key. The settings also held the production domain names and a server IP address. If the live site used that key, **change it** (users are logged out and sessions invalidated).
- The Google Sheet id was hard-coded in the view (and is in the history). It is a document id, not a secret, but it identifies your inventory sheet; it is now configuration.
- A scan of the working tree for private keys, service-account JSON and API keys finds nothing.

## Problems fixed
| Problem | Fix |
|---|---|
| `DEBUG = True`, a literal secret key and the host list in the code | All from the environment; no key means no start in production; `DEBUG` defaults to off; HTTPS redirect, secure cookies, HSTS, `nosniff`, `X-Frame-Options: DENY`, referrer policy |
| Every request to `/inventory/` called the Google Drive API (slow, uses API quota, easy to hammer) and asked for **full read and write access** to the service account's Drive | Exported once per 5 minutes and cached; if Google fails the last good copy is served; the scope is `drive.readonly` |
| The "Live Chat Box" form had no action: **a customer's name, phone number and message were thrown away on submit** | The form posts to `/contact/`, validates the phone number, is CSRF-protected and has a hidden honeypot field against bots; messages are stored and listed in the admin (to be ticked off when handled) |
| The date badge showed the literal word "Date" (nothing ever filled it) | Rendered by the server |
| Tailwind's play CDN (documented as development-only) and Alpine.js loaded from third-party hosts | Tailwind compiled to a 15 KB committed stylesheet, the carousel is 25 lines of JavaScript (it also respects "reduce motion" and shows the first banner without JavaScript) |
| `templates/inventory.html` was never rendered; `inventory/utils.py` (a PDF generator) was never called | Removed |
| The project root was a template directory (`DIRS: [BASE_DIR, ...]`) | Only `templates/` |
| `MEDIA_ROOT` unset (uploads went to the working directory); a file logger wrote every SQL query at DEBUG to an unrotated file created at import | `MEDIA_ROOT` set; logs go to the console |
| Jazzmin was configured for a `books` app and a `make_messages` link that do not exist, and loaded Google Fonts from a CDN | Cleaned; no external fonts |
| `Inventory.__str__` returned `None` for a blank name, which crashes the admin list | Fixed (and tested) |
| `staticfiles/` (191 files) was tracked | Untracked and ignored; WhiteNoise serves static files in production |
| Dependencies: three files, 49 pins, most unused | One `pyproject.toml` + `uv.lock` (47 packages, Django 5.2 LTS) |

## Changes by file
| Path | Change |
|---|---|
| `suffolkcoins/settings.py`, `urls.py`, `settings_test.py`, `manage.py` | environment-driven; test settings; `.env` loaded by `manage.py` |
| `inventory/views.py`, `drive.py`, `forms.py`, `models.py`, `admin.py`, `urls.py`, `migrations/0003_contactmessage.py` | cached export, contact form, `ContactMessage`; existing tables untouched |
| `inventory/utils.py`, `templates/inventory.html`, `Pipfile`, `Pipfile.lock`, `requirements.txt`, `credentials.json`, `staticfiles/` | removed from git (the key stays on disk) |
| `templates/*`, `static/js/carousel.js`, `static/css/site.css`, `assets/site.css`, `package.json` | rewritten without third-party scripts |
| `tests/` | 66 tests |
| `Dockerfile`, `.dockerignore`, `.github/workflows/ci.yml`, `.env.example`, `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore` | new or updated |
| `README.md`, `VERSIONS.md`, `work-done.md` | written to match the code |

## Verification (actual runs)
- `uv run pytest`: **66 passed**, 95% coverage; `ruff` and `bandit` clean; `makemigrations --check` finds no drift.
- Mutation checks (the defect put back, the suite must fail), 17, all caught: Drive scope widened, no cache, no last-good copy, error text in the log, phone check removed, honeypot ignored, `/contact/` accepting GET, wrong status for "not set up", `__str__` crash, messages addable by hand, `DEBUG` on by default, HTTPS hardening off, project folder as template directory, no secret key required, CSRF removed, a CDN script back in the page, the "Date" word back. A typo in `.env.example` is caught by its own test. One real bug found by a test: ordinary phone numbers like `(631) 555-0100` were rejected by my first pattern.
- Real server: production gunicorn on a fresh database (see VERSIONS.md for the list), the Docker image and container, and screenshots at desktop and phone width.
- A count-only scan of the history: the key and the secret key are each in one commit (see above); no other key-shaped strings.
- **Not verified:** the Google export itself (needs the live account and sheet); a GitHub Actions run.

## Needs your attention
- **Rotate the Google key and change `SECRET_KEY`** (first section).
- **On the live server set `ALLOWED_HOSTS`** (the domain names are no longer in the code) and `SECRET_KEY`; without them the site refuses to start or refuses every request. Set `INVENTORY_SHEET_ID` and `GOOGLE_APPLICATION_CREDENTIALS` (the old `credentials.json` next to the code is not read any more), and run `migrate` (one new table).
- If the site is served over plain HTTP, set `HTTPS_ONLY=false`; the default now redirects to HTTPS.
- **Customer messages now contain names and phone numbers.** Decide who may read them and for how long you keep them; there is no deletion feature other than the admin.
- The form is still headed "Live Chat Box" and the page says to "use live chat box", as before, but it is not live chat: the owner reads the message later. The wording is yours to change.
- The contact details of a named person are part of the page (`templates/partials/navbar.html`); I left them as they were.
- The `Inventory` upload model still exists but nothing shows its files (the public list comes from the sheet); it was kept so no data is lost.
- Nothing pushed. To publish: `git push -u origin chore/modernize`
