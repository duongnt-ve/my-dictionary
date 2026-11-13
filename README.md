# My Dictionary

Run the Django backend from the repository root:

```bash
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