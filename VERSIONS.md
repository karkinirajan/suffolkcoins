# Versions

Read from `uv.lock`, `package-lock.json` and the installed packages on 2026-11-02.

| Component | Version | Was | Where it is set |
|---|---|---|---|
| Python | 3.13 (3.13.18 here) | 3.11 (`Pipfile`) | `.python-version`, `pyproject.toml`, `Dockerfile` |
| Django | 5.2.18 (long-term support) | 4.2.6 | `pyproject.toml` (`>=5.2,<5.3`) |
| django-jazzmin | 3.0.5 | 2.6.0 | |
| google-api-python-client | 2.201.0 | 2.105.0 | |
| google-auth | 2.62.0 | 2.23.3 | |
| gunicorn / WhiteNoise | 26.2.0 / 6.12.0 | absent | static files and the server |
| python-dotenv | 1.2.4 | 1.0.0 (installed, never used) | `manage.py` |
| pytest / pytest-django / pytest-cov (dev) | 9.2.0 / 4.14.0 / 7.1.0 | absent | |
| ruff / bandit (dev) | 0.17.3 / 1.9.4 | absent / 1.7.5 | |
| Tailwind CSS (build tool) | 4.3.3 | the Tailwind "play" CDN script (development only), unpinned | `package.json`; output committed |
| uv (in the image) | 0.13.6 | | `Dockerfile` |

47 packages are locked. The old `requirements.txt` pinned 49, of which only Django, django-jazzmin and the Google client packages were used; the rest (`Spire.Xls`, `Spire.XLS-for-Python`, `xlsx2pdf`, `openpyxl`, `reportlab`, `GitPython`, `bandit` as a runtime package, `gspread`, `oauth2client`, `Pillow`, `PyYAML`, ...) belonged to code that was removed or never existed. There were three dependency files (`Pipfile`, `Pipfile.lock`, `requirements.txt`); there is one now.

**Removed from the pages:** Alpine.js 3.2.3 and the Tailwind play CDN (both loaded from third-party hosts), replaced by 25 lines of JavaScript and a compiled 15 KB stylesheet.

## Verified here

- 66 tests pass (95% of lines of `inventory` and `suffolkcoins`); ruff and bandit are clean; no migration drift.
- Production `gunicorn` with `DEBUG` off after `collectstatic` and `migrate` on a fresh database: the page, the hashed WhiteNoise-served stylesheet, script and images, security headers, a refused `Host`, the CSRF-protected contact form (valid, invalid, no token), and the stored message.
- The Docker image builds (804 MB, non-root), applies migrations, serves the site, and holds no key file, tests or `.env`.
- Screenshots of the page at desktop and phone width (Electron's Chromium) look right.

## Not verified here

- The export from Google itself: it needs a live service account and sheet. The code around it (scope, caching, last-good copy, error mapping) is tested with the Drive client replaced.
- A GitHub Actions run, and real-world email or call-back handling of the stored messages.
