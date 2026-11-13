# My Dictionary

## Local setup

Install Docker with Compose, Python, and Node.js. From the repository root:

1. Copy the settings from `.env.example` into `.env` (preserving any existing
   settings) and set `POSTGRES_PASSWORD` to a password for your local database.
   Django and Compose both read this file; environment variables take
   precedence. Do not commit `.env`.
2. Start PostgreSQL and install the backend dependencies:

```bash
docker compose up -d
.venv/bin/python -m pip install -r requirements.txt
```

Once `docker compose ps` shows PostgreSQL as healthy, run:

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

In another terminal, run the React frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite. Its development proxy forwards `/api` requests
to Django at `http://127.0.0.1:8000`. The `/api/words/` endpoint currently
returns sample data, not database records.

PostgreSQL data persists in the Compose `postgres_data` volume. Use
`docker compose down` to stop the container without deleting the data. The
database name, user and password are applied only when the volume is first
initialized; changing them later does not update an existing database. The
PostgreSQL database starts empty: existing `db.sqlite3` data is not imported
automatically. `database/init.sql` is not used by this setup; Django migrations
create the application tables.

## Authentication API

All endpoints accept JSON. Signup creates a Django user with a normalized,
lowercase email as its username; passwords are checked against Django's password
validators. Existing Django users whose username is not their email cannot sign
in through this API.

- `POST /api/auth/signup/`: `{"email": "...", "password": "..."}`; returns
  the email on success.
- `POST /api/auth/signin/`: `{"email": "...", "password": "..."}`; returns
  `access` and `refresh` JWTs.
- `POST /api/auth/refresh/`: `{"refresh": "..."}`; returns a new access token.
- `POST /api/auth/signout/`: `{"refresh": "..."}`; revokes the refresh token.

Access tokens expire after five minutes and refresh tokens after seven days.
Signing out prevents further refreshes, but an already issued access token
remains valid until it expires. The frontend stores the refresh token in
`localStorage` to keep users signed in across browser restarts; JavaScript
running on the site can access it, so XSS is a security risk. This is a
development setup: use HTTPS and production-safe Django settings, and consider
HttpOnly cookies and login rate limiting before deployment.

## Word Search API

- `POST /api/word/search/`: `{"word": "...", "target_lang": "es"}` (anonymous
  allowed); returns `{"word": "...", "translation": "...", "target_lang": "..."}`.
  Authenticated users' searches are stored in the database.
- `GET /api/word/search-history/`: (authenticated only); returns
  `{"searches": [{"id": ..., "word": "...", "result": {...}, "created_at": "..."}, ...]}`.

Translations use the Google Cloud Translation API. Set `GOOGLE_TRANSLATE_API_KEY` in
`.env` to enable search; obtain a key from https://cloud.google.com/translate/docs/setup.
Common language codes: `es` (Spanish), `fr` (French), `de` (German), `ja` (Japanese),
`zh-CN` (Chinese). See [supported languages](https://cloud.google.com/translate/docs/languages)
for the full list.

