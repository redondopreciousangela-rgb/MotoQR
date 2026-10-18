# MotoQR — Motorcycle Rental System

Web app (multi-device) + desktop Tkinter client.

## Online access (any device)

### Local / classroom Wi‑Fi

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` on this machine, or `http://YOUR-LAN-IP:5000` on phones/laptops on the same Wi‑Fi.

### Deploy free on Render (public HTTPS link)

1. Push this repo to GitHub.
2. Go to [https://render.com](https://render.com) → **New** → **Web Service**.
3. Connect the `MotoQR` repository.
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Add env var `SECRET_KEY` (any random string).
6. Deploy. Share the `https://….onrender.com` URL.

Anyone with the link can open it on phone, tablet, or laptop.

### Demo accounts

| Role  | Username | Password |
|-------|----------|----------|
| Admin | `admin`  | `1234`   |
| Client| register a new account |

## Features

- Browse fleet & rent (Cash / GCash / Card)
- Admin payment confirmation + notifications
- Return requests approve/reject
- Simulated GPS tracker for active rentals
- Overdue detection + ₱100/day late fee
- JSON data under `data/`

## Desktop app (optional)

```bash
python rental.py
```

Requires: `pillow`, `qrcode`, optional `opencv-python` for webcam ID capture.
