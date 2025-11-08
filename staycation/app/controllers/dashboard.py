from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from app import db
from models.book import Booking
from models.package import Package
from utils.checks import admin_required

def _as_dt(x):
    if isinstance(x, datetime):
        return x
    try:
        return datetime.strptime(str(x), "%Y-%m-%d")
    except Exception:
        return datetime.fromisoformat(str(x))

def _month_iter(start_dt: datetime, end_dt: datetime):
    cur = datetime(start_dt.year, start_dt.month, 1)
    end = datetime(end_dt.year, end_dt.month, 1)
    while cur <= end:
        yield (cur.year, cur.month), cur.strftime("%b %Y")
        # +1 month
        if cur.month == 12:
            cur = datetime(cur.year + 1, 1, 1)
        else:
            cur = datetime(cur.year, cur.month + 1, 1)

dashboard = Blueprint('dashboard', __name__)

@dashboard.route("/dashboard", methods=["GET"])
@login_required
@admin_required
def dashboard_home():
    # Empty page with dropdown (Figure Q4a)
    return render_template("dashboard.html", panel="CHART")

@dashboard.route("/dashboard/bookings_by_month", methods=["POST"])
@login_required
@admin_required
def dashboard_bookings_by_month():
    """
    Returns counts per month-year per hotel for a grouped bar chart.
    Response shape:
      { "hotels": [...], "months": [...], "matrix": [[...], ...] }
      where matrix[i][j] = count for months[i] at hotels[j]
    """
    # collect all bookings
    bookings = Booking.objects()  # includes those uploaded in Q2(b) if present

    # canonical month label "MMM YYYY"
    def month_key(dt):
        d = dt if isinstance(dt, datetime) else datetime.strptime(str(dt), "%Y-%m-%d")
        return d.strftime("%b %Y")

    # hotels list sorted A–Z
    hotels = sorted({b.package.hotel_name for b in bookings})

    # month axis sorted by date ascending
    month_set = {}
    for b in bookings:
        d = b.check_in_date if isinstance(b.check_in_date, datetime) else datetime.strptime(str(b.check_in_date), "%Y-%m-%d")
        month_set[(d.year, d.month)] = d.strftime("%b %Y")
    # ensure at least one month to avoid empty chart
    months = [month_set[k] for k in sorted(month_set.keys())]

    # initialize matrix: rows = months, cols = hotels
    idx_h = {h:i for i,h in enumerate(hotels)}
    idx_m = {m:i for i,m in enumerate(months)}
    matrix = [[0 for _ in hotels] for __ in months]

    for b in bookings:
        h = b.package.hotel_name
        m = month_key(b.check_in_date)
        if h in idx_h and m in idx_m:
            matrix[idx_m[m]][idx_h[h]] += 1

    return jsonify({"hotels": hotels, "months": months, "matrix": matrix})

@dashboard.route('/trend_chart', methods=['GET', 'POST'])
def trend_chart():
    if request.method == 'GET':
        return render_template('trend_chart.html', panel="Package Chart")

    # --- MONTHLY aggregation for "Amount Incoming" ---
    from collections import defaultdict

    bookings = Booking.getAllBookings()

    if not bookings:
        return jsonify({"labels": [], "series": []})

    # hotel -> {(YYYY,M) -> total_amount}
    from collections import defaultdict
    hotel_month_sum = defaultdict(lambda: defaultdict(float))
    dates = []

    for b in bookings:
        dt = _as_dt(b.check_in_date)
        dates.append(dt)
        ym = (dt.year, dt.month)
        hotel = b.package.hotel_name
        hotel_month_sum[hotel][ym] += float(b.total_cost or 0.0)

    start, end = min(dates), max(dates)
    axis_pairs, labels = zip(*list(_month_iter(start, end)))
    month_axis = list(axis_pairs)            # [(YYYY,M), ...]
    labels     = list(labels)                # ["Jan 2022", ...]

    series = []
    for hotel in sorted(hotel_month_sum.keys()):
        row = [hotel_month_sum[hotel].get(ym, 0.0) for ym in month_axis]
        series.append({"label": hotel, "data": row})

    return jsonify({"labels": labels, "series": series})