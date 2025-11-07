from flask_login import login_user, login_required, logout_user, current_user
from flask import Blueprint, request, redirect, render_template, url_for, flash
from models.package import Package
from models.bundle import BundlePurchase

from models.forms import BookForm

from models.users import User
from models.package import Package

package = Blueprint('packageController', __name__)

@package.route('/')
@package.route('/packages')
def packages():
    all_packages = Package.getAllPackages()
    return render_template('packages.html', panel="Package", all_packages=all_packages)

@package.route("/viewPackageDetail/<hotel_name>")
def viewPackageDetail(hotel_name):
    the_package = Package.getPackage(hotel_name=hotel_name)
    return render_template('packageDetail.html', panel="Package Detail", package=the_package)

@package.route('/purchaseBundle', methods=['POST'])
@login_required
def purchaseBundle():
    # block admins; only non-admin users may purchase bundles
    if current_user.email == "admin@abc.com":
        flash("This is a non-admin function. Please log in as a non-admin user to use this function.", "info")
        return redirect(url_for('packageController.packages'))

    selected_ids = request.form.getlist('package_ids')  # list of package ObjectIds from checkboxes
    if not selected_ids:
        flash("Please select packages to buy as a bundle", "warning")
        return redirect(url_for('packageController.packages'))

    # load selected packages and compute total before discount
    packages, total = [], 0.0
    for pid in selected_ids:
        p = Package.objects(id=pid).first()
        if p:
            packages.append(p)
            total += float(p.packageCost())

    # determine discount tier
    n = len(packages)
    if n == 1:
        rate = 0.0
    elif n in (2, 3):
        rate = 0.10
    else:
        rate = 0.20

    discount = total * rate
    discounted_total = total - discount

    # save bundle purchase with current date and all items unused
    BundlePurchase.create_for_user(current_user, packages)

    # flash outcome message like the figures
    names = ", ".join([p.hotel_name for p in packages])
    if n == 1:
        msg = f"No discount for bundle purchase for {names}<br>Total cost ${total:0.2f}"
    else:
        msg = f"{int(rate*100)}% discount for bundle purchase for {names}<br>Total cost ${total:0.2f}<br>Discounted total ${discounted_total:0.2f}"
    flash(msg, "info")
    return redirect(url_for('packageController.packages'))