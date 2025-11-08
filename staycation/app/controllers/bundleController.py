from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, redirect, url_for, flash

from models.bundle import BundlePurchase
from models.book import Booking
from models.package import Package

from datetime import datetime
from utils.checks import non_admin_required
bundle = Blueprint('bundleController', __name__)  # use bundleController.fn

@bundle.route('/manageBundle', methods=['GET'])
@login_required
@non_admin_required
def manage_bundle():
    # Load bundles sorted by purchase date (ascending)
    bundles = BundlePurchase.for_user_sorted(current_user)
    return render_template('manageBundle.html', panel="Manage Bundles", bundles=bundles)

@bundle.route('/manageBundle/book', methods=['POST'])
@login_required
@non_admin_required
def book_from_bundle():
    bundle_id  = request.form.get('bundle_id')
    package_id = request.form.get('package_id')
    check_in   = request.form.get('check_in_date')

    bp = BundlePurchase.objects(id=bundle_id, customer=current_user).first()
    if not bp:
        flash("Bundle not found.", "warning")
        return redirect(url_for('bundleController.manage_bundle'))

    if bp.is_expired():
        flash("This bundle has expired.", "warning")
        return redirect(url_for('bundleController.manage_bundle'))

    # Server-side guard: check-in cannot be before purchase date
    try:
        ci_dt = datetime.strptime(check_in, "%Y-%m-%d")
    except Exception:
        flash("Invalid date.", "warning")
        return redirect(url_for('bundleController.manage_bundle'))

    # Normalize purchase date to date precision
    purchase_dt = bp.purchased_date.replace(hour=0, minute=0, second=0, microsecond=0)
    if ci_dt < purchase_dt:
        flash("Check-in date cannot be earlier than the bundle purchase date.", "warning")
        return redirect(url_for('bundleController.manage_bundle'))

    pkg = Package.objects(id=package_id).first()
    if not pkg:
        flash("Package not found.", "warning")
        return redirect(url_for('bundleController.manage_bundle'))

    Booking.createBooking(check_in, current_user, pkg)
    bp.mark_utilised(str(package_id))

    flash("Booking created from bundle.", "info")
    return redirect(url_for('bundleController.manage_bundle'))

