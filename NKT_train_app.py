# NKT_train_app.py
"""
Single-file Flask app: NKT-Train (fake availability, no external API)
Usage:
  - pip install -r requirements.txt
  - python3 NKT_train_app.py
  - Open the provided URL (Replit or http://127.0.0.1:5000 if running locally)
This version generates plausible fake availability results from inputs.
"""
from flask import Flask, request, render_template_string
from datetime import datetime, timedelta
import random

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<title>NKT-Train - Seat Availability (Demo)</title>
<h1>NKT-Train - Check Seat Availability (Demo)</h1>
<form method=post action="{{ url_for('search') }}">
  <label>Train Number: <input name="train_number" required></label><br><br>
  <label>Journey Date (YYYY-MM-DD): <input name="journey_date" required placeholder="2026-06-20"></label><br><br>
  <label>Boarding Station (code): <input name="source" required placeholder="NDLS"></label><br><br>
  <label>Deboarding Station (code): <input name="dest" required placeholder="BCT"></label><br><br>
  <label>Coach Type:
    <select name="coach">
      <option>SL</option>
      <option>3E</option>
      <option>3A</option>
      <option>2A</option>
      <option>1A</option>
      <option>CC</option>
      <option>2S</option>
    </select>
  </label><br><br>
  <input type=submit value="Check Availability">
</form>
<p>This is a demo app that generates simulated availability so you can test the UI without signing up for any API.</p>
"""

RESULT_HTML = """
<!doctype html>
<title>Results - NKT-Train (Demo)</title>
<h1>Availability result (Demo)</h1>
<p><strong>Train:</strong> {{ train }}</p>
<p><strong>Date:</strong> {{ date }}</p>
<p><strong>From:</strong> {{ source }} → <strong>To:</strong> {{ dest }}</p>
<p><strong>Coach:</strong> {{ coach }}</p>

<table border="1" cellpadding="6" cellspacing="0">
  <tr><th>Quota</th><th>Coach</th><th>Date</th><th>Availability</th><th>Message</th></tr>
  {% for row in availability %}
    <tr>
      <td>{{ row.quota }}</td>
      <td>{{ row.coach }}</td>
      <td>{{ row.date }}</td>
      <td>{{ row.available }}</td>
      <td>{{ row.message }}</td>
    </tr>
  {% endfor %}
</table>

<p><a href="{{ url_for('index') }}">Check another</a></p>
"""

COACH_CODES = ["SL", "3E", "3A", "2A", "1A", "CC", "2S"]

def safe_parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def simulate_availability(train, date, source, dest, coach):
    # Produce a deterministic-ish seed so same inputs give same output usually
    seed = hash((train, str(date), source.upper(), dest.upper(), coach)) & 0xffffffff
    rnd = random.Random(seed)

    # produce 5 days surrounding requested date (date-2 .. date+2)
    rows = []
    for dshift in range(-2, 3):
        d = date + timedelta(days=dshift)
        # base availability depends on coach class
        base = {
            "1A": 5,
            "2A": 10,
            "3A": 20,
            "3E": 8,
            "SL": 40,
            "CC": 35,
            "2S": 80
        }.get(coach, 20)
        # adjust by train number parity and day offset
        adj = (int(train[-1]) if train and train[-1].isdigit() else 3) % 7
        variation = rnd.randint(-15, 15)
        available = max(0, base + variation - abs(dshift)*5 - adj)
        # message generation
        if available >= 50:
            msg = "Plenty of seats"
        elif available >= 20:
            msg = "Good availability"
        elif available >= 5:
            msg = "Limited seats"
        elif available > 0:
            msg = "RAC or few WL"
        else:
            msg = "No availability"
        rows.append({
            "quota": "GN",
            "coach": coach,
            "date": d.strftime("%Y-%m-%d"),
            "available": f"{available} seats" if available>0 else "0",
            "message": msg
        })
    # Also add a small "fare" hint for paid classes
    for r in rows:
        if r["coach"] in ("1A", "2A", "3A"):
            r["message"] += f" • est fare ₹{rnd.randint(300,1200)}"
    return rows

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/search", methods=["POST"])
def search():
    train = request.form.get("train_number", "").strip()
    journey_date = request.form.get("journey_date", "").strip()
    source = request.form.get("source", "").strip() or "SRC"
    dest = request.form.get("dest", "").strip() or "DST"
    coach = request.form.get("coach", "").strip().upper()
    if coach not in COACH_CODES:
        coach = "SL"

    date_obj = safe_parse_date(journey_date)
    if not date_obj:
        # fallback: use today
        date_obj = datetime.utcnow().date()

    availability = simulate_availability(train or "00000", date_obj, source, dest, coach)

    return render_template_string(RESULT_HTML,
                                  train=train or "00000",
                                  date=date_obj.strftime("%Y-%m-%d"),
                                  source=source.upper(),
                                  dest=dest.upper(),
                                  coach=coach,
                                  availability=availability)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
