from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from utils.checks import non_admin_required
from models.bundle import BundlePurchase
from models.book import Booking
from models.package import Package

bundleSPA = Blueprint('bundleSPA', __name__)

@bundleSPA.route("/manageBundleSPA", methods=["GET"])
@login_required
@non_admin_required
def manage_bundle_spa():
    # SPA shell (empty page + JS)
    return render_template("manageBundleSPA.html", panel="MANAGE BUNDLES")

def _bundle_to_dict(b: BundlePurchase):
    return {
        "id": str(b.id),
        "purchased_date": b.purchased_date.strftime("%Y-%m-%d"),
        "expiry_date": b.expiry_date.strftime("%Y-%m-%d"),
        "expired": b.is_expired(),
        "items": [
            {
                "package_id": str(it.package.id),
                "hotel_name": it.package.hotel_name,
                "image_url": it.package.image_url,
                "utilised": bool(it.utilised),
            }
            for it in b.bundledPackages
        ],
    }

@bundleSPA.route("/api/bundles", methods=["GET"])
@login_required
@non_admin_required
def api_bundles():
    bundles = BundlePurchase.for_user_sorted(current_user)
    return jsonify([_bundle_to_dict(b) for b in bundles])

@bundleSPA.route("/api/bundle/book", methods=["POST"])
@login_required
@non_admin_required
def api_book_from_bundle():
    data = request.get_json(force=True)
    bundle_id  = data.get("bundle_id")
    package_id = data.get("package_id")
    check_in   = data.get("check_in_date")  # "YYYY-MM-DD"

    bp = BundlePurchase.objects(id=bundle_id, customer=current_user).first()
    if not bp:
        return jsonify({"ok": False, "msg": "Bundle not found."}), 404
    if bp.is_expired():
        return jsonify({"ok": False, "msg": "Bundle expired."}), 400

    try:
        ci_dt = datetime.strptime(check_in, "%Y-%m-%d")
    except Exception:
        return jsonify({"ok": False, "msg": "Invalid date."}), 400

    purchase_dt = bp.purchased_date.replace(hour=0, minute=0, second=0, microsecond=0)
    if ci_dt < purchase_dt:
        return jsonify({"ok": False, "msg": "Check-in before purchase date not allowed."}), 400

    pkg = Package.objects(id=package_id).first()
    if not pkg:
        return jsonify({"ok": False, "msg": "Package not found."}), 404

    Booking.createBooking(ci_dt, current_user, pkg)
    bp.mark_utilised(package_id)

    # return updated bundle so UI can refresh inline
    bp.reload()
    return jsonify({"ok": True, "bundle": _bundle_to_dict(bp)})
