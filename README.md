# University Elections Voting System

A Django-based university student election website (login, home, students,
elections, positions, candidates, voters and ballot pages).

## Group Members

| # | Name | Registration No. |
|---|------|------------------|
| 1 | _Full name_ | _Reg. number_ |
| 2 | _Full name_ | _Reg. number_ |
| 3 | _Full name_ | _Reg. number_ |
| 4 | _Full name_ | _Reg. number_ |

## Run locally

```bash
python -m venv venv
venv\Scripts\activate        # Windows  (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py ensure_admin
python manage.py seed_demo   # optional: loads demo election data
python manage.py runserver
```

Open http://127.0.0.1:8000/ — the Django admin is at `/admin/`.

## Superuser

- Username: `admin`
- Password: `admin123`

Demo accounts created by `seed_demo`: `staff` / `student123` (staff) and
`jmutua`, `kwaweru`, `nchebet` (verified, can vote) and `todhiambo`
(unverified) — all with password `student123`.

## Deployment

Deployed on Render using `render.yaml` / `build.sh`
(the build runs `migrate` and creates the superuser automatically).
