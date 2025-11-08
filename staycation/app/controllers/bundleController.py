from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, redirect, url_for, flash

from models.bundle import BundlePurchase
from models.book import Booking
from models.package import Package

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
    bundle_id   = request.form.get('bundle_id')
    package_id  = request.form.get('package_id')
    check_in    = request.form.get('check_in_date')  # expected 'YYYY-MM-DD'

    # Validate bundle ownership
    bp = BundlePurchase.objects(id=bundle_id, customer=current_user).first()
    if not bp:
        flash("Bundle not found.", "warning")
        return redirect(url_for('bundleController.manage_bundle'))

    # Ensure bundle not expired
    if bp.is_expired():
        flash("This bundle has expired.", "warning")
        return redirect(url_for('bundleController.manage_bundle'))

    # Resolve package
    pkg = Package.objects(id=package_id).first()
    if not pkg:
        flash("Package not found.", "warning")
        return redirect(url_for('bundleController.manage_bundle'))

    # Create booking and mark utilised
    Booking.createBooking(check_in, current_user, pkg)
    bp.mark_utilised(package_id)

    flash("Booking created from bundle and marked as utilised.", "info")
    return redirect(url_for('bundleController.manage_bundle'))

