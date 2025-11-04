# Weather Intel — Full Stack (Flask + Static Map)

This repo serves your RadarMap front-end at `/` and your Python backend under `/api/...`.
Ready to deploy on Render or Railway.

## Contents
- `app.py` — Flask app
- `static/RadarMap-optimized.html` — optimized front-end (replace with your latest if needed)
- `models/` — 1 model file(s) copied from your upload
- `backend/` — Python package for your own modules (import and use from `app.py`)

## Run locally
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python app.py
# open http://127.0.0.1:8000
```

## Deploy to Render
1. Push this folder to a GitHub repo.
2. On Render: New → Web Service → connect the repo.
3. Build Command:
   ```
   pip install -r requirements.txt
   ```
4. Start Command:
   ```
   gunicorn app:app -w 2 -k gevent -b 0.0.0.0:8000
   ```
5. Use the Render HTTPS URL in OBS → Browser Source.

## Notes
- Keep secrets in host env vars (Render → Environment), not in the repo.
- If you have existing endpoints (alerts/outlooks/history), move them into `app.py` or import from `backend/`.
- To use your exact model inference, edit `/api/ml/predictions` accordingly.